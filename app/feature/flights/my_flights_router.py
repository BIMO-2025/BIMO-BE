"""
사용자 비행 기록 (myFlights) API 라우터
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.feature.flights.flights_schemas import MyFlightSchema
from app.feature.flights.my_flights_service import MyFlightsService
from app.core.security import verify_firebase_token
from app.core.deps import get_firebase_service
from app.core.firebase import FirebaseService

router = APIRouter(
    prefix="/users/{user_id}/my-flights",
    tags=["My Flights"],
    responses={404: {"description": "Not found"}},
)

security = HTTPBearer()


def get_my_flights_service(
    firebase_service: FirebaseService = Depends(get_firebase_service)
) -> MyFlightsService:
    """MyFlightsService 의존성 주입"""
    return MyFlightsService(firebase_service=firebase_service)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_id: str = None
) -> str:
    """
    Firebase 토큰에서 사용자 ID를 추출하고 검증합니다.
    
    Args:
        credentials: HTTP Bearer 토큰
        user_id: 경로 파라미터의 사용자 ID
        
    Returns:
        사용자 ID
        
    Raises:
        HTTPException: 토큰이 유효하지 않거나 사용자 ID가 일치하지 않는 경우
    """
    token = credentials.credentials
    decoded_token = verify_firebase_token(token)
    
    token_user_id = decoded_token.get("uid")
    
    # 경로의 user_id와 토큰의 user_id가 일치하는지 확인
    if user_id and token_user_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="이 리소스에 접근할 권한이 없습니다"
        )
    
    return token_user_id or user_id


@router.post("", response_model=dict)
async def create_my_flight(
    user_id: str,
    flight_data: MyFlightSchema,
    current_user_id: str = Depends(get_current_user_id),
    service: MyFlightsService = Depends(get_my_flights_service)
):
    """
    사용자의 비행 기록을 생성합니다.
    
    - **flightNumber**: 항공편 번호 (예: "KE901")
    - **airlineCode**: 항공사 코드 (예: "KE")
    - **departureTime**: 출발 시간 (ISO 8601 형식)
    - **arrivalTime**: 도착 시간 (ISO 8601 형식)
    - **status**: 비행 상태 ("scheduled" 또는 "completed")
    - **reviewId**: 리뷰 ID (선택적)
    """
    flight_id = await service.create_flight(user_id, flight_data)
    return {"id": flight_id, "message": "비행 기록이 생성되었습니다."}


@router.get("", response_model=List[MyFlightSchema])
async def get_my_flights(
    user_id: str,
    status: Optional[str] = Query(None, description="비행 상태 필터 (scheduled/completed)"),
    limit: int = Query(20, ge=1, le=100, description="조회할 최대 개수"),
    current_user_id: str = Depends(get_current_user_id),
    service: MyFlightsService = Depends(get_my_flights_service)
):
    """
    사용자의 비행 기록 목록을 조회합니다.
    
    - **status**: 비행 상태 필터 (선택적)
    - **limit**: 조회할 최대 개수 (기본값: 20, 최대: 100)
    - 최신 출발 시간순으로 정렬됩니다.
    """
    flights = await service.get_flights(user_id, status, limit)
    return flights


@router.get("/{flight_id}", response_model=MyFlightSchema)
async def get_my_flight(
    user_id: str,
    flight_id: str,
    current_user_id: str = Depends(get_current_user_id),
    service: MyFlightsService = Depends(get_my_flights_service)
):
    """
    특정 비행 기록을 조회합니다.
    
    - **flight_id**: 비행 기록 ID
    """
    flight = await service.get_flight_by_id(user_id, flight_id)
    if not flight:
        raise HTTPException(status_code=404, detail="비행 기록을 찾을 수 없습니다.")
    return flight


@router.put("/{flight_id}", response_model=dict)
async def update_my_flight(
    user_id: str,
    flight_id: str,
    update_data: dict,
    current_user_id: str = Depends(get_current_user_id),
    service: MyFlightsService = Depends(get_my_flights_service)
):
    """
    비행 기록을 업데이트합니다.
    
    - **update_data**: 업데이트할 필드와 값
    """
    success = await service.update_flight(user_id, flight_id, update_data)
    if not success:
        raise HTTPException(status_code=404, detail="비행 기록을 찾을 수 없습니다.")
    return {"message": "비행 기록이 업데이트되었습니다."}


@router.delete("/{flight_id}", response_model=dict)
async def delete_my_flight(
    user_id: str,
    flight_id: str,
    current_user_id: str = Depends(get_current_user_id),
    service: MyFlightsService = Depends(get_my_flights_service)
):
    """
    비행 기록을 삭제합니다.
    
    - **flight_id**: 비행 기록 ID
    """
    success = await service.delete_flight(user_id, flight_id)
    if not success:
        raise HTTPException(status_code=404, detail="비행 기록을 찾을 수 없습니다.")
    return {"message": "비행 기록이 삭제되었습니다."}





