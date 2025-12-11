"""
항공편 검색 관련 API 라우터
"""

from fastapi import APIRouter, Depends

from app.core.deps import get_firebase_service, get_amadeus_client
from app.core.firebase import FirebaseService
from app.feature.flights import flights_schemas
from app.feature.flights.flights_service import FlightsService

router = APIRouter(
    prefix="/flights",
    tags=["Flights"],
    responses={404: {"description": "Not found"}},
)


def get_flights_service(
    firebase_service: FirebaseService = Depends(get_firebase_service),
    amadeus_client = Depends(get_amadeus_client)
) -> FlightsService:
    """FlightsService 의존성 주입"""
    return FlightsService(
        amadeus_client=amadeus_client,
        firebase_service=firebase_service
    )


@router.post("/search", response_model=flights_schemas.FlightSearchResponse)
async def search_flights(
    request: flights_schemas.FlightSearchRequest,
    service: FlightsService = Depends(get_flights_service)
):
    """
    출발지, 도착지, 날짜를 기반으로 예약 가능한 항공편을 검색합니다.

    - **origin**: 출발지 공항 코드 (예: ICN, JFK, LAX)
    - **destination**: 도착지 공항 코드 (예: ICN, JFK, LAX)
    - **departure_date**: 출발 날짜 (YYYY-MM-DD 형식)
    - **adults**: 성인 승객 수 (기본값: 1, 최대: 9)

    Amadeus API를 사용하여 실시간 항공편 정보를 조회합니다. (편도 검색만 지원)
    """
    return await service.search_flights(request)

@router.get("/locations", response_model=flights_schemas.LocationSearchResponse)
async def search_locations(
    keyword: str,
    service: FlightsService = Depends(get_flights_service)
):
    """
    키워드로 공항 및 도시를 검색합니다.
    
    - **keyword**: 검색어 (예: "Seoul", "JFK", "London")
    
    도시와 공항 정보를 모두 반환합니다.
    """
    return await service.search_locations(keyword)
