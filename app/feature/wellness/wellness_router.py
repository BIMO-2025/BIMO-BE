"""
시차적응 및 피로도 관리 API 라우터
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.feature.wellness import flight_timeline_schemas, flight_timeline_service
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
    firebase_service = Depends(get_firebase_service)
) -> MyFlightsService:
    """MyFlightsService 의존성 주입"""
    return MyFlightsService(firebase_service=firebase_service)


@router.post("/flight-timeline", response_model=flight_timeline_schemas.FlightTimelineResponse)
async def generate_flight_timeline(request: flight_timeline_schemas.FlightTimelineRequest):
    """
    LLM을 사용하여 비행 타임라인을 생성합니다.
    
    사용자의 비행 정보(출발지, 도착지, 출발/도착 시간)와 비행 목표를 기반으로
    최적의 기내 활동 타임라인을 생성합니다.
    
    - **origin**: 출발 공항 코드 (예: DXB)
    - **destination**: 도착 공항 코드 (예: ICN)
    - **departure_time**: 출발 시간 (ISO 8601 형식)
    - **arrival_time**: 도착 시간 (ISO 8601 형식)
    - **seat_class**: 좌석 등급 (ECONOMY, BUSINESS, FIRST 등)
    - **flight_goal**: 비행 목표 (SLEEP_FOCUS, WORK_FOCUS, ENTERTAINMENT 등)
    - **total_duration**: 총 비행 시간 (선택사항, 예: "9h 30m")
    
    Returns:
        - **flight_info**: 비행 정보 요약
        - **recommendation_message**: 사용자에게 보여줄 추천 메시지
        - **timeline_events**: 타임라인 이벤트 목록 (이륙, 식사, 수면, 자유시간, 착륙 등)
    """
    return await flight_timeline_service.generate_flight_timeline(request)




@router.post("/users/{user_id}/my-flights/{flight_id}/timeline", response_model=flight_timeline_schemas.FlightTimelineResponse)
async def generate_flight_timeline_from_my_flight(
    user_id: str,
    flight_id: str,
    flight_goal: str = Query(..., description="비행 목표 (SLEEP_FOCUS, WORK_FOCUS, ENTERTAINMENT)"),
    seat_class: str = Query("ECONOMY", description="좌석 등급"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    my_flights_service: MyFlightsService = Depends(get_my_flights_service)
):
    """
    myFlights에 저장된 비행 정보를 기반으로 비행 타임라인을 생성합니다.
    
    - **user_id**: 사용자 ID
    - **flight_id**: myFlights에 저장된 비행 기록 ID
    - **flight_goal**: 비행 목표 (SLEEP_FOCUS, WORK_FOCUS, ENTERTAINMENT)
    - **seat_class**: 좌석 등급 (기본값: ECONOMY)
    
    Returns:
        - **flight_info**: 비행 정보 요약
        - **recommendation_message**: 추천 메시지
        - **timeline_events**: 타임라인 이벤트 목록
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
        
    # FlightTimelineRequest 생성
    # MyFlightSchema의 최상위 필드 사용
    request = flight_timeline_schemas.FlightTimelineRequest(
        origin=my_flight.departureAirport or "Unknown",
        destination=my_flight.arrivalAirport or "Unknown",
        departure_time=my_flight.departureTime,
        arrival_time=my_flight.arrivalTime,
        seat_class=seat_class,
        flight_goal=flight_goal
    )
    
    # 타임라인 생성 서비스 호출
    return await flight_timeline_service.generate_flight_timeline(request)
