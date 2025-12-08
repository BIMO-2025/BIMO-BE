from typing import List
from fastapi import APIRouter, Depends, Query
from app.feature.flights.destination_service import DestinationService
from app.feature.airlines.models import Airport

router = APIRouter(prefix="/destinations", tags=["destinations"])

def get_destination_service():
    return DestinationService()

@router.get("/search", response_model=List[Airport])
async def search_destinations(
    query: str = Query(..., min_length=1, description="국가, 도시, 공항명, 공항코드 검색"),
    service: DestinationService = Depends(get_destination_service)
):
    """
    목적지 검색
    """
    return await service.search_destinations(query)
