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


# 기존 Amadeus 기반 엔드포인트는 제거됨
# @router.post("/search", response_model=flights_schemas.FlightSearchResponse)
# async def search_flights(...):
#     ...


@router.post("/search/airlines", response_model=flights_schemas.AirlineSearchResponse)
async def search_airlines_flights(
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
