from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from app.feature.airlines.airline_service import AirlineService
from app.feature.airlines.models import Airline, AirlineDetail

router = APIRouter(prefix="/airlines", tags=["airlines"])

def get_airline_service():
    return AirlineService()

@router.get("/search", response_model=List[Airline])
async def search_airlines(
    query: str = Query(..., min_length=1, description="검색할 항공사 이름"),
    service: AirlineService = Depends(get_airline_service)
):
    """
    항공사 검색
    """
    return await service.search_airlines(query)

@router.get("/popular", response_model=List[Airline])
async def get_popular_airlines(
    limit: int = 5,
    service: AirlineService = Depends(get_airline_service)
):
    """
    인기 항공사 목록 조회 (기본: 평점순)
    """
    return await service.get_popular_airlines(limit)

@router.get("/{airline_id}", response_model=AirlineDetail)
async def get_airline_detail(
    airline_id: str,
    service: AirlineService = Depends(get_airline_service)
):
    """
    항공사 상세 정보 조회
    """
    airline = await service.get_airline_detail(airline_id)
    if not airline:
        raise HTTPException(status_code=404, detail="Airline not found")
    return airline
