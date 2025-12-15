from typing import Optional
import asyncio
import logging
from datetime import datetime

from fastapi.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.exceptions.exceptions import AppConfigError, ExternalApiError

# 로거 설정
logger = logging.getLogger(__name__)


class AmadeusClient:
    """
    Amadeus API SDK 초기화 및 항공편 검색 요청 실행을 담당하는 어댑터.
    """

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        environment: str | None = None,
    ) -> None:
        if api_key is None:
            api_key = settings.AMADEUS_API_KEY
        if api_secret is None:
            api_secret = settings.AMADEUS_API_SECRET
        if environment is None:
            environment = settings.AMADEUS_ENVIRONMENT
        self._import_sdk()
        self._configure(api_key, api_secret, environment)

    @staticmethod
    def _import_sdk():
        try:
            # Amadeus SDK import 확인
            import amadeus
            return amadeus
        except ModuleNotFoundError as exc:
            raise AppConfigError(
                "필수 패키지 'amadeus'가 설치되지 않았습니다. "
                "pip install amadeus 로 설치하세요."
            ) from exc

    def _configure(
        self, api_key: str | None, api_secret: str | None, environment: str | None
    ) -> None:
        if not api_key or not api_secret:
            raise AppConfigError(
                "환경 변수 'AMADEUS_API_KEY'와 'AMADEUS_API_SECRET'이 설정되지 않았습니다. .env를 확인하세요."
            )

        # Amadeus 클라이언트 초기화
        try:
            from amadeus import Client
        except ImportError:
            raise AppConfigError(
                "Amadeus Client를 import할 수 없습니다. amadeus 패키지가 올바르게 설치되었는지 확인하세요."
            )

        # test 환경은 'test', production 환경은 'production' 사용
        is_production = environment == "production"
        self.client = Client(
            client_id=api_key,
            client_secret=api_secret,
            hostname=(
                "production" if is_production else "test"
            ),  # 'test' 또는 'production'
        )

    @staticmethod
    def _extract_error_info(exception) -> dict:
        """
        Amadeus API 에러에서 상세 정보 추출
        
        Returns:
            dict with keys: status_code, error_code, title, detail, is_retryable
        """
        error_info = {
            "status_code": None,
            "error_code": None,
            "title": None,
            "detail": str(exception),
            "is_retryable": False
        }
        
        # status_code 추출
        if hasattr(exception, "response"):
            if hasattr(exception.response, "status_code"):
                error_info["status_code"] = exception.response.status_code
            
            # response body 파싱
            if hasattr(exception.response, "body"):
                body = exception.response.body
                if isinstance(body, dict):
                    errors = body.get("errors", [])
                    if errors and len(errors) > 0:
                        first_error = errors[0]
                        error_info["error_code"] = first_error.get("code")
                        error_info["title"] = first_error.get("title")
                        error_info["detail"] = first_error.get("detail", error_info["detail"])
        
        # 재시도 가능 여부 판단
        if error_info["status_code"] in [500, 502, 503, 504]:
            error_info["is_retryable"] = True
        elif error_info["error_code"] in [141, 38187]:  # System error, timeout
            error_info["is_retryable"] = True
        
        return error_info
    
    @staticmethod
    def _get_user_friendly_message(error_info: dict) -> str:
        """
        사용자 친화적인 에러 메시지 생성
        """
        status = error_info["status_code"]
        code = error_info["error_code"]
        
        # 상태 코드별 메시지
        if status == 400:
            return "검색 조건이 올바르지 않습니다. 날짜와 공항 코드를 확인해주세요."
        elif status == 401:
            return "API 인증에 실패했습니다. 서비스 관리자에게 문의하세요."
        elif status == 404:
            return "요청하신 항공편 정보를 찾을 수 없습니다."
        elif status == 429:
            return "요청 한도를 초과했습니다. 잠시 후 다시 시도해주세요."
        elif status in [500, 502, 503]:
            return "항공편 검색 서비스가 일시적으로 불안정합니다. 잠시 후 다시 시도해주세요."
        
        # 에러 코드별 메시지
        if code == 141:
            return "항공편 데이터를 처리하는 중 오류가 발생했습니다. 다른 날짜나 노선을 시도해보세요."
        elif code == 477:
            return "해당 노선에 대한 항공편 정보가 없습니다."
        elif code == 38187:
            return "검색 요청 시간이 초과되었습니다. 다시 시도해주세요."
        
        return f"항공편 검색 중 오류가 발생했습니다: {error_info.get('title', '알 수 없는 오류')}"

    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        adults: int = 1,
        return_date: Optional[str] = None,
        max_retries: int = 3,
    ) -> dict:
        """
        항공편을 검색합니다. (재시도 로직 포함)

        Args:
            origin: 출발지 공항 코드 (예: "ICN", "JFK")
            destination: 도착지 공항 코드 (예: "ICN", "JFK")
            departure_date: 출발 날짜 (YYYY-MM-DD 형식)
            adults: 성인 승객 수 (기본값: 1)
            return_date: 귀국 날짜 (선택사항, YYYY-MM-DD 형식)
            max_retries: 최대 재시도 횟수 (기본값: 3)

        Returns:
            검색된 항공편 정보를 담은 딕셔너리

        Raises:
            ExternalApiError: Amadeus API 호출 중 오류 발생 시
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # 동기 Amadeus API 호출을 비동기로 실행
                def _search():
                    if return_date:
                        # 왕복 항공편 검색
                        response = self.client.shopping.flight_offers_search.get(
                            originLocationCode=origin.upper(),
                            destinationLocationCode=destination.upper(),
                            departureDate=departure_date,
                            returnDate=return_date,
                            adults=adults,
                            max=50,  # 최대 50개 결과 반환
                        )
                    else:
                        # 편도 항공편 검색
                        response = self.client.shopping.flight_offers_search.get(
                            originLocationCode=origin.upper(),
                            destinationLocationCode=destination.upper(),
                            departureDate=departure_date,
                            adults=adults,
                            max=50,  # 최대 50개 결과 반환
                        )

                    # 응답 데이터 반환
                    if hasattr(response, "data"):
                        return response.data
                    elif isinstance(response, dict) and "data" in response:
                        return response["data"]
                    else:
                        return response

                response = await run_in_threadpool(_search)
                
                # 성공 시 로그
                if attempt > 0:
                    logger.info(f"Amadeus API 재시도 성공 (시도: {attempt + 1}/{max_retries})")
                
                return response

            except Exception as exc:
                last_error = exc
                error_info = self._extract_error_info(exc)
                
                # 로그 기록
                logger.warning(
                    f"Amadeus API 오류 (시도 {attempt + 1}/{max_retries}): "
                    f"Status={error_info['status_code']}, "
                    f"Code={error_info['error_code']}, "
                    f"Title={error_info['title']}"
                )
                
                # 재시도 가능 여부 확인
                if error_info["is_retryable"] and attempt < max_retries - 1:
                    # Exponential backoff
                    wait_time = (2 ** attempt) * 0.5  # 0.5s, 1s, 2s
                    logger.info(f"Amadeus API 재시도 대기 중... ({wait_time}초)")
                    await asyncio.sleep(wait_time)
                    continue
                
                # 재시도 불가능하거나 마지막 시도 실패
                user_message = self._get_user_friendly_message(error_info)
                raise ExternalApiError(
                    provider="Amadeus",
                    detail=user_message,
                ) from exc
        
        # 모든 재시도 실패
        if last_error:
            error_info = self._extract_error_info(last_error)
            user_message = self._get_user_friendly_message(error_info)
            raise ExternalApiError(
                provider="Amadeus",
                detail=f"{user_message} (재시도 {max_retries}회 실패)",
            ) from last_error

    async def search_locations(
        self,
        keyword: str,
        sub_type: list[str] = ["AIRPORT", "CITY"],
        max_retries: int = 2,
    ) -> list[dict]:
        """
        키워드로 공항 및 도시를 검색합니다. (재시도 로직 포함)
        
        Args:
            keyword: 검색 키워드 (예: "Seoul", "JFK")
            sub_type: 검색 대상 유형 리스트 (기본값: ["AIRPORT", "CITY"])
            max_retries: 최대 재시도 횟수 (기본값: 2)
            
        Returns:
            검색된 위치 정보 리스트
            
        Raises:
            ExternalApiError: Amadeus API 호출 중 오류 발생 시
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                def _search():
                    response = self.client.reference_data.locations.get(
                        keyword=keyword,
                        subType=",".join(sub_type)
                    )
                    
                    if hasattr(response, "data"):
                        return response.data
                    elif isinstance(response, dict) and "data" in response:
                        return response["data"]
                    else:
                        return response

                response = await run_in_threadpool(_search)
                return response if isinstance(response, list) else []

            except Exception as exc:
                last_error = exc
                error_info = self._extract_error_info(exc)
                
                logger.warning(
                    f"Amadeus 위치 검색 오류 (시도 {attempt + 1}/{max_retries}): "
                    f"Status={error_info['status_code']}"
                )
                
                # 재시도 가능 여부 확인
                if error_info["is_retryable"] and attempt < max_retries - 1:
                    wait_time = 0.5 * (attempt + 1)
                    await asyncio.sleep(wait_time)
                    continue
                
                # 재시도 불가능하거나 마지막 시도
                user_message = self._get_user_friendly_message(error_info)
                raise ExternalApiError(
                    provider="Amadeus",
                    detail=user_message,
                ) from exc
        
        # 모든 재시도 실패
        if last_error:
            raise ExternalApiError(
                provider="Amadeus",
                detail="위치 검색 중 오류가 발생했습니다.",
            ) from last_error


# =============================================================================
# 하위 호환성을 위한 모듈 레벨 변수 (deprecated)
# 새로운 코드에서는 AmadeusClient를 직접 인스턴스화하거나 DI를 사용하세요.
# =============================================================================

# Lazy initialization을 위한 변수
_amadeus_client = None


def get_amadeus_client() -> AmadeusClient:
    """
    Amadeus 클라이언트 인스턴스를 반환합니다.
    
    Returns:
        AmadeusClient 인스턴스
    """
    global _amadeus_client
    if _amadeus_client is None:
        _amadeus_client = AmadeusClient()
    return _amadeus_client


# 하위 호환성을 위해: 모듈 import 시 자동 초기화하지 않음
# 대신 필요할 때 get_amadeus_client() 호출
amadeus_client = None  # deprecated: get_amadeus_client()를 사용하세요

__all__ = ["AmadeusClient", "get_amadeus_client", "amadeus_client"]

