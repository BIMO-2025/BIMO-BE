"""
항공편 검색 관련 비즈니스 로직
"""

from app.feature.flights import amadeus_client
from app.feature.flights.flights_schemas import (
    FlightSearchRequest,
    FlightSearchResponse,
    FlightOfferSchema,
)
from app.core.exceptions.exceptions import ExternalApiError


async def search_flights(request: FlightSearchRequest) -> FlightSearchResponse:
    """
    Amadeus API를 사용하여 항공편을 검색합니다.

    Args:
        request: 항공편 검색 요청 정보
            - origin: 출발지 공항 코드
            - destination: 도착지 공항 코드
            - departure_date: 출발 날짜
            - adults: 성인 승객 수

    Returns:
        검색된 항공편 제안 목록

    Raises:
        ExternalApiError: Amadeus API 호출 중 오류 발생 시
    """
    try:
        # Amadeus API 호출 (편도 검색만 지원)
        flight_data = await amadeus_client.search_flights(
            origin=request.origin,
            destination=request.destination,
            departure_date=request.departure_date,
            adults=request.adults,
        )

        # 응답 데이터가 리스트가 아닌 경우 처리
        if not isinstance(flight_data, list):
            flight_data = flight_data if isinstance(flight_data, list) else []

        # Pydantic 모델로 변환
        flight_offers = []
        for offer in flight_data:
            try:
                # Amadeus 응답을 FlightOfferSchema로 변환
                flight_offer = FlightOfferSchema(**offer)
                flight_offers.append(flight_offer)
            except Exception as e:
                # 개별 항공편 파싱 실패 시 로그만 남기고 계속 진행
                print(f"항공편 제안 파싱 실패: {e}")
                continue

        return FlightSearchResponse(
            flight_offers=flight_offers,
            count=len(flight_offers),
        )

    except ExternalApiError:
        # ExternalApiError는 그대로 재발생
        raise
    except Exception as e:
        # 기타 예외는 ExternalApiError로 변환
        raise ExternalApiError(
            provider="Amadeus",
            detail=f"항공편 검색 중 오류가 발생했습니다: {str(e)}",
        ) from e

