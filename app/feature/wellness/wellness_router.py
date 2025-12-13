"""
시차적응 및 피로도 관리 API 라우터
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.feature.wellness import wellness_schemas, wellness_service
from app.feature.flights.my_flights_service import MyFlightsService
from app.core.deps import get_firebase_service
from app.core.firebase import FirebaseService
from app.core.security import verify_firebase_token

router = APIRouter(
    prefix="/wellness",
    tags=["Wellness"],
    responses={404: {"description": "Not found"}},
)

security = HTTPBearer()


def get_my_flights_service(
    firebase_service: FirebaseService = Depends(get_firebase_service)
) -> MyFlightsService:
    """MyFlightsService 의존성 주입"""
    return MyFlightsService(firebase_service=firebase_service)


@router.post("/jetlag-plan", response_model=wellness_schemas.JetLagPlanResponse)
async def generate_jetlag_plan(request: wellness_schemas.JetLagPlanRequest):
    """
    LLM을 사용하여 시차적응 계획을 생성합니다.
    
    사용자의 출발 시간, 도착 시간, 경유지, 도착지 시간대 등을 고려하여
    최적의 피로도 관리를 위한 시차적응 계획을 생성합니다.
    
    - **flight_segments**: 비행 구간 목록 (최소 1개)
    - **destination_timezone**: 도착지 시간대 (예: "America/New_York")
    - **origin_timezone**: 출발지 시간대 (선택사항, 예: "Asia/Seoul")
    - **user_sleep_pattern_start**: 사용자 평소 수면 시작 시간 (선택사항, HH:MM 형식)
    - **user_sleep_pattern_end**: 사용자 평소 수면 종료 시간 (선택사항, HH:MM 형식)
    - **trip_duration_days**: 여행 기간 (선택사항, 기본값: 7일)
    
    Returns:
        - **origin_timezone**: 출발지 시간대
        - **destination_timezone**: 도착지 시간대
        - **time_difference_hours**: 시차 (시간 단위)
        - **total_flight_duration_hours**: 총 비행 시간
        - **daily_schedules**: 일별 일정 (수면 시간, 식사 시간, 활동 등)
        - **general_recommendations**: 일반적인 권장사항
        - **pre_flight_tips**: 출발 전 팁
        - **post_arrival_tips**: 도착 후 팁
        - **algorithm_explanation**: LLM이 생성한 알고리즘 설명
    """
    return await wellness_service.generate_jetlag_plan(request)


@router.post("/users/{user_id}/my-flights/{flight_id}/jetlag-plan", response_model=wellness_schemas.JetLagPlanResponse)
async def generate_jetlag_plan_from_my_flight(
    user_id: str,
    flight_id: str,
    destination_timezone: str,
    origin_timezone: str = None,
    user_sleep_pattern_start: str = None,
    user_sleep_pattern_end: str = None,
    trip_duration_days: int = None,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    my_flights_service: MyFlightsService = Depends(get_my_flights_service)
):
    """
    myFlights에 저장된 비행 정보를 기반으로 시차적응 계획을 생성합니다.
    
    - **user_id**: 사용자 ID
    - **flight_id**: myFlights에 저장된 비행 기록 ID
    - **destination_timezone**: 도착지 시간대 (예: "America/New_York")
    - **origin_timezone**: 출발지 시간대 (선택사항, 예: "Asia/Seoul")
    - **user_sleep_pattern_start**: 사용자 평소 수면 시작 시간 (선택사항, HH:MM 형식)
    - **user_sleep_pattern_end**: 사용자 평소 수면 종료 시간 (선택사항, HH:MM 형식)
    - **trip_duration_days**: 여행 기간 (선택사항, 기본값: 7일)
    
    Returns:
        - **origin_timezone**: 출발지 시간대
        - **destination_timezone**: 도착지 시간대
        - **time_difference_hours**: 시차 (시간 단위)
        - **total_flight_duration_hours**: 총 비행 시간
        - **daily_schedules**: 일별 일정 (수면 시간, 식사 시간, 활동 등)
        - **general_recommendations**: 일반적인 권장사항
        - **pre_flight_tips**: 출발 전 팁
        - **post_arrival_tips**: 도착 후 팁
        - **algorithm_explanation**: LLM이 생성한 알고리즘 설명
    """
    # 인증 확인
    token = credentials.credentials
    decoded_token = verify_firebase_token(token)
    token_user_id = decoded_token.get("uid")
    
    if token_user_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to access this resource"
        )
    
    # myFlights에서 비행 정보 조회
    my_flight = await my_flights_service.get_flight_by_id(user_id, flight_id)
    if not my_flight:
        raise HTTPException(
            status_code=404,
            detail="비행 기록을 찾을 수 없습니다."
        )
    
    # MyFlightSchema를 FlightSegment로 변환
    try:
        flight_segment = wellness_service.convert_my_flight_to_segment(my_flight)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    
    # JetLagPlanRequest 생성
    request = wellness_schemas.JetLagPlanRequest(
        flight_segments=[flight_segment],
        destination_timezone=destination_timezone,
        origin_timezone=origin_timezone,
        user_sleep_pattern_start=user_sleep_pattern_start,
        user_sleep_pattern_end=user_sleep_pattern_end,
        trip_duration_days=trip_duration_days
    )
    
    # 시차적응 계획 생성
    return await wellness_service.generate_jetlag_plan(request)


