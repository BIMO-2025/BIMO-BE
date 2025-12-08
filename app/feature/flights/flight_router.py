from typing import List
from fastapi import APIRouter, Depends, Query, Header, HTTPException
from app.feature.flights.flight_service import FlightService
from app.feature.flights.models import MyFlight, MyFlightCreate, FlightStats

router = APIRouter(prefix="/flights", tags=["flights"])

def get_flight_service():
    return FlightService()

# 데모용: 실제 로그인 연동 전 임시 User ID 추출 함수
async def get_current_user_id(authorization: str = Header(None)) -> str:
    if not authorization:
        # 데모 편의를 위해 토큰 없으면 데모 유저 ID 리턴 (프로덕션 절대 금지)
        return "demo_user_123" 
    token = authorization.replace("Bearer ", "")
    # 실제 jwt decode 필요
    return token.replace("demo_token_", "")

@router.post("/my-flights", response_model=MyFlight)
async def add_my_flight(
    flight_data: MyFlightCreate,
    user_id: str = Depends(get_current_user_id),
    service: FlightService = Depends(get_flight_service)
):
    """내 비행 등록"""
    return await service.add_flight(user_id, flight_data)

@router.get("/my-flights/upcoming", response_model=List[MyFlight])
async def get_upcoming_flights(
    user_id: str = Depends(get_current_user_id),
    service: FlightService = Depends(get_flight_service)
):
    """예정된 비행 목록"""
    return await service.get_upcoming_flights(user_id)

@router.get("/my-flights/past", response_model=List[MyFlight])
async def get_past_flights(
    user_id: str = Depends(get_current_user_id),
    service: FlightService = Depends(get_flight_service)
):
    """지난 비행 목록 (완료된 비행)"""
    return await service.get_past_flights(user_id)

@router.get("/stats", response_model=FlightStats)
async def get_flight_stats(
    user_id: str = Depends(get_current_user_id),
    service: FlightService = Depends(get_flight_service)
):
    """비행 통계"""
    return await service.get_stats(user_id)
