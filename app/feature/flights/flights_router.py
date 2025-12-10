"""
항공편 검색 관련 API 라우터
"""

from fastapi import APIRouter

from app.feature.flights import flights_schemas, flights_service

router = APIRouter(
    prefix="/flights",
    tags=["Flights"],
    responses={404: {"description": "Not found"}},
)


@router.post("/search", response_model=flights_schemas.FlightSearchResponse)
async def search_flights(request: flights_schemas.FlightSearchRequest):
    """
    출발지, 도착지, 날짜를 기반으로 예약 가능한 항공편을 검색합니다.

    - **origin**: 출발지 공항 코드 (예: ICN, JFK, LAX)
    - **destination**: 도착지 공항 코드 (예: ICN, JFK, LAX)
    - **departure_date**: 출발 날짜 (YYYY-MM-DD 형식)
    - **adults**: 성인 승객 수 (기본값: 1, 최대: 9)

    Amadeus API를 사용하여 실시간 항공편 정보를 조회합니다. (편도 검색만 지원)
    """
    return await flights_service.search_flights(request)

@router.get("/locations", response_model=flights_schemas.LocationSearchResponse)
async def search_locations(keyword: str):
    """
    키워드로 공항 및 도시를 검색합니다.
    
    - **keyword**: 검색어 (예: "Seoul", "JFK", "London")
    
    도시와 공항 정보를 모두 반환합니다.
    """
    return await flights_service.search_locations(keyword)
