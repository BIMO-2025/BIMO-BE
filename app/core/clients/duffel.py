from typing import Optional
import asyncio
import logging
from datetime import datetime

from fastapi.concurrency import run_in_threadpool
import httpx

from app.core.config import settings
from app.core.exceptions.exceptions import AppConfigError, ExternalApiError

# 로거 설정
logger = logging.getLogger(__name__)


class DuffelClient:
    """
    Duffel API 클라이언트
    항공편 검색 요청 실행을 담당하는 어댑터.
    """

    def __init__(
        self,
        api_key: str | None = None,
        environment: str | None = None,
    ) -> None:
        if api_key is None:
            api_key = settings.DUFFEL_API_KEY
        if environment is None:
            environment = settings.DUFFEL_ENVIRONMENT
        
        self._configure(api_key, environment)

    def _configure(
        self, api_key: str | None, environment: str | None
    ) -> None:
        if not api_key:
            raise AppConfigError(
                "환경 변수 'DUFFEL_API_KEY'가 설정되지 않았습니다. .env를 확인하세요."
            )

        # Duffel API base URL 설정
        if environment == "production":
            self.base_url = "https://api.duffel.com"
        else:
            self.base_url = "https://api.duffel.com"  # Duffel은 test/production이 같은 URL
        
        self.api_key = api_key
        self.environment = environment or "test"
        
        # HTTP 클라이언트 설정
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Duffel-Version": "v2",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    @staticmethod
    def _extract_error_info(exception) -> dict:
        """
        Duffel API 에러에서 상세 정보 추출
        
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
        
        # httpx.HTTPStatusError 처리
        if isinstance(exception, httpx.HTTPStatusError):
            error_info["status_code"] = exception.response.status_code
            
            try:
                body = exception.response.json()
                if isinstance(body, dict):
                    errors = body.get("errors", [])
                    if errors and len(errors) > 0:
                        first_error = errors[0]
                        error_info["error_code"] = first_error.get("code")
                        error_info["title"] = first_error.get("title")
                        error_info["detail"] = first_error.get("detail", error_info["detail"])
            except Exception:
                error_info["detail"] = exception.response.text or str(exception)
        
        # httpx.RequestError 처리
        elif isinstance(exception, httpx.RequestError):
            error_info["detail"] = f"요청 오류: {str(exception)}"
        
        # 재시도 가능 여부 판단
        if error_info["status_code"] in [500, 502, 503, 504]:
            error_info["is_retryable"] = True
        elif error_info["status_code"] == 429:  # Rate limit
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
        
        return f"항공편 검색 중 오류가 발생했습니다: {error_info.get('title', '알 수 없는 오류')}"

    async def search_offers(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        adults: int = 1,
        max_retries: int = 3,
    ) -> dict:
        """
        Duffel API를 사용하여 항공편을 검색합니다. (재시도 로직 포함)

        Args:
            origin: 출발지 공항 코드 (예: "ICN", "JFK")
            destination: 도착지 공항 코드 (예: "ICN", "JFK")
            departure_date: 출발 날짜 (YYYY-MM-DD 형식)
            adults: 성인 승객 수 (기본값: 1)
            max_retries: 최대 재시도 횟수 (기본값: 3)

        Returns:
            검색된 항공편 정보를 담은 딕셔너리 (offer_requests.create 응답)

        Raises:
            ExternalApiError: Duffel API 호출 중 오류 발생 시
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Offer Request 생성
                request_data = {
                    "data": {
                        "slices": [
                            {
                                "origin": origin.upper(),
                                "destination": destination.upper(),
                                "departure_date": departure_date,
                            }
                        ],
                        "passengers": [
                            {"type": "adult"} for _ in range(adults)
                        ],
                        "cabin_class": "economy",
                    }
                }
                
                response = await self.client.post(
                    "/air/offer_requests",
                    json=request_data,
                )
                response.raise_for_status()
                
                result = response.json()
                
                # 성공 시 로그
                if attempt > 0:
                    logger.info(f"Duffel API 재시도 성공 (시도: {attempt + 1}/{max_retries})")
                
                return result

            except httpx.HTTPStatusError as exc:
                last_error = exc
                error_info = self._extract_error_info(exc)
                
                # 로그 기록
                logger.warning(
                    f"Duffel API 오류 (시도 {attempt + 1}/{max_retries}): "
                    f"Status={error_info['status_code']}, "
                    f"Code={error_info['error_code']}, "
                    f"Title={error_info['title']}"
                )
                
                # 재시도 가능 여부 확인
                if error_info["is_retryable"] and attempt < max_retries - 1:
                    # Exponential backoff
                    wait_time = (2 ** attempt) * 0.5  # 0.5s, 1s, 2s
                    logger.info(f"Duffel API 재시도 대기 중... ({wait_time}초)")
                    await asyncio.sleep(wait_time)
                    continue
                
                # 재시도 불가능하거나 마지막 시도 실패
                user_message = self._get_user_friendly_message(error_info)
                raise ExternalApiError(
                    provider="Duffel",
                    detail=user_message,
                ) from exc
                
            except httpx.RequestError as exc:
                last_error = exc
                error_info = self._extract_error_info(exc)
                
                logger.warning(
                    f"Duffel API 요청 오류 (시도 {attempt + 1}/{max_retries}): {str(exc)}"
                )
                
                # 네트워크 오류는 재시도 가능
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 0.5
                    logger.info(f"Duffel API 재시도 대기 중... ({wait_time}초)")
                    await asyncio.sleep(wait_time)
                    continue
                
                raise ExternalApiError(
                    provider="Duffel",
                    detail="항공편 검색 서비스에 연결할 수 없습니다. 잠시 후 다시 시도해주세요.",
                ) from exc
                
            except Exception as exc:
                last_error = exc
                logger.error(f"Duffel API 예상치 못한 오류: {str(exc)}")
                
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 0.5
                    await asyncio.sleep(wait_time)
                    continue
                
                raise ExternalApiError(
                    provider="Duffel",
                    detail=f"항공편 검색 중 오류가 발생했습니다: {str(exc)}",
                ) from exc
        
        # 모든 재시도 실패
        if last_error:
            error_info = self._extract_error_info(last_error)
            user_message = self._get_user_friendly_message(error_info)
            raise ExternalApiError(
                provider="Duffel",
                detail=f"{user_message} (재시도 {max_retries}회 실패)",
            ) from last_error

    async def search_places(
        self,
        query: str,
        max_retries: int = 2,
    ) -> list[dict]:
        """
        Duffel API를 사용하여 장소(공항, 도시 등)를 검색합니다. (재시도 로직 포함)

        Args:
            query: 검색 쿼리 (도시명, 국가명 등, 예: "Seoul South Korea")
            max_retries: 최대 재시도 횟수 (기본값: 2)

        Returns:
            검색된 장소 정보 리스트

        Raises:
            ExternalApiError: Duffel API 호출 중 오류 발생 시
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # GET /places/suggestions 호출
                response = await self.client.get(
                    "/places/suggestions",
                    params={"query": query},
                )
                response.raise_for_status()
                
                result = response.json()
                
                # 성공 시 로그
                if attempt > 0:
                    logger.info(f"Duffel API 재시도 성공 (시도: {attempt + 1}/{max_retries})")
                
                # 응답에서 data 추출
                places = result.get("data", [])
                return places if isinstance(places, list) else []

            except httpx.HTTPStatusError as exc:
                last_error = exc
                error_info = self._extract_error_info(exc)
                
                # 로그 기록
                logger.warning(
                    f"Duffel API 장소 검색 오류 (시도 {attempt + 1}/{max_retries}): "
                    f"Status={error_info['status_code']}, "
                    f"Code={error_info['error_code']}, "
                    f"Title={error_info['title']}"
                )
                
                # 재시도 가능 여부 확인
                if error_info["is_retryable"] and attempt < max_retries - 1:
                    # Exponential backoff
                    wait_time = (2 ** attempt) * 0.5  # 0.5s, 1s
                    logger.info(f"Duffel API 재시도 대기 중... ({wait_time}초)")
                    await asyncio.sleep(wait_time)
                    continue
                
                # 재시도 불가능하거나 마지막 시도 실패
                user_message = self._get_user_friendly_message(error_info)
                raise ExternalApiError(
                    provider="Duffel",
                    detail=user_message,
                ) from exc
                
            except httpx.RequestError as exc:
                last_error = exc
                error_info = self._extract_error_info(exc)
                
                logger.warning(
                    f"Duffel API 요청 오류 (시도 {attempt + 1}/{max_retries}): {str(exc)}"
                )
                
                # 네트워크 오류는 재시도 가능
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 0.5
                    logger.info(f"Duffel API 재시도 대기 중... ({wait_time}초)")
                    await asyncio.sleep(wait_time)
                    continue
                
                raise ExternalApiError(
                    provider="Duffel",
                    detail="장소 검색 서비스에 연결할 수 없습니다. 잠시 후 다시 시도해주세요.",
                ) from exc
                
            except Exception as exc:
                last_error = exc
                logger.error(f"Duffel API 예상치 못한 오류: {str(exc)}")
                
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 0.5
                    await asyncio.sleep(wait_time)
                    continue
                
                raise ExternalApiError(
                    provider="Duffel",
                    detail=f"장소 검색 중 오류가 발생했습니다: {str(exc)}",
                ) from exc
        
        # 모든 재시도 실패
        if last_error:
            error_info = self._extract_error_info(last_error)
            user_message = self._get_user_friendly_message(error_info)
            raise ExternalApiError(
                provider="Duffel",
                detail=f"{user_message} (재시도 {max_retries}회 실패)",
            ) from last_error

    async def close(self):
        """HTTP 클라이언트 종료"""
        await self.client.aclose()


# =============================================================================
# 하위 호환성을 위한 모듈 레벨 변수
# =============================================================================

# Lazy initialization을 위한 변수
_duffel_client = None


def get_duffel_client() -> DuffelClient:
    """
    Duffel 클라이언트 인스턴스를 반환합니다.
    
    Returns:
        DuffelClient 인스턴스
    """
    global _duffel_client
    if _duffel_client is None:
        _duffel_client = DuffelClient()
    return _duffel_client


__all__ = ["DuffelClient", "get_duffel_client"]

