"""
항공편 검색 관련 API 라우터
"""

from fastapi import APIRouter, Depends

from app.core.deps import get_firebase_service, get_duffel_client
from app.core.firebase import FirebaseService
from app.feature.flights import flights_schemas
from app.feature.flights.flights_service import FlightsService

router = APIRouter(
    prefix="/flights",
    tags=["Flights"],
    responses={404: {"description": "Not found"}},
)

# 별도 라우터: /search/airlines 엔드포인트용
search_router = APIRouter(
    prefix="/search",
    tags=["Search"],
    responses={404: {"description": "Not found"}},
)


def get_flights_service(
    firebase_service = Depends(get_firebase_service),
    duffel_client = Depends(get_duffel_client)
) -> FlightsService:
    """FlightsService 의존성 주입"""
    return FlightsService(
        duffel_client=duffel_client,
        firebase_service=firebase_service
    )





@search_router.post("/airlines", response_model=flights_schemas.AirlineSearchResponse)
async def search_airlines(
    request: flights_schemas.AirlineSearchRequest,
    service: FlightsService = Depends(get_flights_service)
):
    """
    출발지, 도착지, 날짜를 기반으로 동일한 operating carrier를 가진 항공편을 검색합니다.

    - **departure**: 출발지 공항 IATA 코드 (예: ICN)
    - **arrive**: 도착지 공항 IATA 코드 (예: JFK)
    - **departure_date**: 출발 날짜 (YYYY-MM-DD 형식)

    Duffel API를 사용하여 실시간 항공편 정보를 조회합니다.
    동일한 operating carrier를 가진 항공편만 반환됩니다.
    """
    return await service.search_airlines(request)


@search_router.get("/airportIATACode", response_model=flights_schemas.AirportIATASearchResponse)
async def search_airport_iata_code(
    location: str,
    service: FlightsService = Depends(get_flights_service)
):
    """
    위치 정보로 공항 IATA 코드를 검색합니다.

    - **location**: 위치 정보 (도시명, 국가명 등, 예: "Seoul" 또는 "Seoul South Korea")

    Duffel API를 사용하여 공항 정보를 조회합니다.
    """
    request = flights_schemas.AirportIATASearchRequest(location=location)
    return await service.search_airport_iata_code(request)


