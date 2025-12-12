from typing import Optional

from fastapi.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.exceptions.exceptions import AppConfigError, ExternalApiError


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

    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        adults: int = 1,
        return_date: Optional[str] = None,
    ) -> dict:
        """
        항공편을 검색합니다.

        Args:
            origin: 출발지 공항 코드 (예: "ICN", "JFK")
            destination: 도착지 공항 코드 (예: "ICN", "JFK")
            departure_date: 출발 날짜 (YYYY-MM-DD 형식)
            adults: 성인 승객 수 (기본값: 1)
            return_date: 귀국 날짜 (선택사항, YYYY-MM-DD 형식)

        Returns:
            검색된 항공편 정보를 담은 딕셔너리

        Raises:
            ExternalApiError: Amadeus API 호출 중 오류 발생 시
        """
        try:
            # 동기 Amadeus API 호출을 비동기로 실행
            def _search():
                try:
                    if return_date:
                        # 왕복 항공편 검색
                        response = self.client.shopping.flight_offers_search.get(
                            originLocationCode=origin.upper(),
                            destinationLocationCode=destination.upper(),
                            departureDate=departure_date,
                            returnDate=return_date,
                            adults=adults,
                            max=100,  # 최대 100개 결과 반환
                            sort="-price",  # 가격 높은순 정렬
                        )
                    else:
                        # 편도 항공편 검색
                        response = self.client.shopping.flight_offers_search.get(
                            originLocationCode=origin.upper(),
                            destinationLocationCode=destination.upper(),
                            departureDate=departure_date,
                            adults=adults,
                            max=100,  # 최대 100개 결과 반환
                            sort="-price",  # 가격 높은순 정렬
                        )

                    # 응답 데이터 반환
                    if hasattr(response, "data"):
                        return response.data
                    elif isinstance(response, dict) and "data" in response:
                        return response["data"]
                    else:
                        return response
                except Exception as api_exc:
                    # Amadeus SDK의 ResponseError 등 상세 에러 정보 추출
                    error_details = str(api_exc)
                    if hasattr(api_exc, "response"):
                        if hasattr(api_exc.response, "body"):
                            error_details += f" | Response: {api_exc.response.body}"
                        if hasattr(api_exc.response, "status_code"):
                            error_details += f" | Status: {api_exc.response.status_code}"
                    if hasattr(api_exc, "description"):
                        error_details += f" | Description: {api_exc.description}"
                    raise Exception(error_details) from api_exc

            response = await run_in_threadpool(_search)
            return response

        except ExternalApiError:
            raise
        except Exception as exc:
            error_message = str(exc)
            raise ExternalApiError(
                provider="Amadeus",
                detail=f"항공편 검색 중 오류가 발생했습니다: {error_message}",
            ) from exc

    async def search_locations(
        self,
        keyword: str,
        sub_type: list[str] = ["AIRPORT", "CITY"]
    ) -> list[dict]:
        """
        키워드로 공항 및 도시를 검색합니다.
        
        Args:
            keyword: 검색 키워드 (예: "Seoul", "JFK")
            sub_type: 검색 대상 유형 리스트 (기본값: ["AIRPORT", "CITY"])
            
        Returns:
            검색된 위치 정보 리스트
            
        Raises:
            ExternalApiError: Amadeus API 호출 중 오류 발생 시
        """
        try:
            def _search():
                try:
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
                except Exception as api_exc:
                     # Amadeus SDK의 ResponseError 등 상세 에러 정보 추출
                    error_details = str(api_exc)
                    if hasattr(api_exc, "response"):
                        if hasattr(api_exc.response, "body"):
                            error_details += f" | Response: {api_exc.response.body}"
                        if hasattr(api_exc.response, "status_code"):
                            error_details += f" | Status: {api_exc.response.status_code}"
                    if hasattr(api_exc, "description"):
                        error_details += f" | Description: {api_exc.description}"
                    raise Exception(error_details) from api_exc

            response = await run_in_threadpool(_search)
            return response if isinstance(response, list) else []

        except ExternalApiError:
            raise
        except Exception as exc:
            raise ExternalApiError(
                provider="Amadeus",
                detail=f"위치 검색 중 오류가 발생했습니다: {str(exc)}",
            ) from exc


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

