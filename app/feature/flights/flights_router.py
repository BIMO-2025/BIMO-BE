"""
항공편 검색 API 라우터
"""

from fastapi import APIRouter, Depends, Query
from app.feature.flights.flights_schemas import FlightSearchResponse
from app.feature.flights.flights_service import get_flight_service, FlightService

router = APIRouter(prefix="/flights", tags=["flights"])

@router.get("/search", response_model=FlightSearchResponse)
async def search_flights(
    origin: str = Query(..., description="출발지 공항 코드 (예: ICN)"),
    destination: str = Query(..., description="도착지 공항 코드 (예: JFK)"),
    date: str = Query(..., description="출발 날짜 (YYYY-MM-DD)"),
    service: FlightService = Depends(get_flight_service)
):
    """
    항공편 검색 API
    
    - **origin**: 출발지 공항 코드 (IATA 3자리)
    - **destination**: 도착지 공항 코드 (IATA 3자리)
    - **date**: 출발 날짜 (YYYY-MM-DD)
    """
    return service.search_flights(origin, destination, date)
