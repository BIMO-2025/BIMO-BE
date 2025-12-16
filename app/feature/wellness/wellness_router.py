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
        
    # segments를 FlightSegmentInfo로 변환
    flight_segments = None
    if my_flight.segments and len(my_flight.segments) > 0:
        flight_segments = []
        for seg in my_flight.segments:
            # departure와 arrival에서 시간 추출
            dep_dict = seg.departure if isinstance(seg.departure, dict) else {}
            arr_dict = seg.arrival if isinstance(seg.arrival, dict) else {}
            
            dep_time_str = dep_dict.get("at")
            arr_time_str = arr_dict.get("at")
            
            # 시간 파싱
            from datetime import datetime
            if dep_time_str and arr_time_str:
                if isinstance(dep_time_str, str):
                    dep_time = datetime.fromisoformat(dep_time_str.replace("Z", "+00:00"))
                else:
                    dep_time = dep_time_str
                    
                if isinstance(arr_time_str, str):
                    arr_time = datetime.fromisoformat(arr_time_str.replace("Z", "+00:00"))
                else:
                    arr_time = arr_time_str
                
                flight_segments.append(
                    flight_timeline_schemas.FlightSegmentInfo(
                        origin=dep_dict.get("iata_code") or dep_dict.get("iataCode", ""),
                        destination=arr_dict.get("iata_code") or arr_dict.get("iataCode", ""),
                        departure_time=dep_time,
                        arrival_time=arr_time,
                        duration=seg.duration or "0h 0m"
                    )
                )
    
    # FlightTimelineRequest 생성
    request = flight_timeline_schemas.FlightTimelineRequest(
        origin=my_flight.departureAirport or "Unknown",
        destination=my_flight.arrivalAirport or "Unknown",
        departure_time=my_flight.departureTime,
        arrival_time=my_flight.arrivalTime,
        seat_class=seat_class,
        flight_goal=flight_goal,
        segments=flight_segments if flight_segments else None,  # segments 정보 추가
        has_stopover=my_flight.hasStopover  # 경유 여부 추가
    )
    
    # 타임라인 생성 서비스 호출
    return await flight_timeline_service.generate_flight_timeline(request)

