"""
시차적응 및 피로도 관리 API 라우터
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.feature.wellness import flight_timeline_schemas, flight_timeline_service
from app.feature.flights.my_flights_service import MyFlightsService
from app.feature.users.user_service import UserService
from app.core.deps import get_firebase_service
from app.core.firebase import FirebaseService
from app.core.security import decode_access_token
from app.core.exceptions.exceptions import InvalidTokenError

router = APIRouter(
    prefix="/wellness",
    tags=["Wellness"],
    responses={404: {"description": "Not found"}},
)

security = HTTPBearer()

def _normalize_flight_goal(raw_goal: str | None) -> str:
    """
    클라이언트 입력(영문 Enum 또는 한글 자연어)을 서버 내부 목표 문자열로 정규화합니다.
    Swagger(OpenAPI)에는 노출하지 않고 서버에서 기본값을 처리하기 위해 라우터 레벨에서 수행합니다.
    """
    if not raw_goal:
        return "SLEEP_FOCUS"

    goal = str(raw_goal).strip()
    if not goal:
        return "SLEEP_FOCUS"

    upper = goal.upper()
    if upper in {"SLEEP_FOCUS", "WORK_FOCUS", "ENTERTAINMENT"}:
        return upper

    # 한글/자연어 입력에 대한 보수적 매핑 (미매칭 시 기본값)
    if ("시차" in goal) or ("적응" in goal) or ("수면" in goal) or ("잠" in goal):
        return "SLEEP_FOCUS"
    if ("업무" in goal) or ("일" in goal) or ("작업" in goal) or ("WORK" in upper):
        return "WORK_FOCUS"
    if ("휴식" in goal) or ("오락" in goal) or ("엔터" in goal) or ("ENTERTAIN" in upper):
        return "ENTERTAINMENT"

    return "SLEEP_FOCUS"


def get_my_flights_service(
    firebase_service = Depends(get_firebase_service)
) -> MyFlightsService:
    """MyFlightsService 의존성 주입"""
    return MyFlightsService(firebase_service=firebase_service)







@router.post("/users/{user_id}/my-flights/{flight_id}/timeline", response_model=flight_timeline_schemas.FlightTimelineResponse)
async def generate_flight_timeline_from_my_flight(
    user_id: str,
    flight_id: str,
    request: Request,
    flight_goal_query: str | None = Query(None, include_in_schema=False),
    seat_class: str = Query("ECONOMY", description="좌석 등급"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    my_flights_service: MyFlightsService = Depends(get_my_flights_service)
):
    """
    myFlights에 저장된 비행 정보를 기반으로 비행 타임라인을 생성합니다.
    
    - **user_id**: 사용자 ID
    - **flight_id**: myFlights에 저장된 비행 기록 ID
    - **seat_class**: 좌석 등급 (기본값: ECONOMY)
    - **flight_goal**: (선택) JSON body로 전달 가능. Swagger에는 노출되지 않으며 서버가 기본값으로 처리합니다.
    
    Returns:
        - **flight_info**: 비행 정보 요약
        - **recommendation_message**: 추천 메시지
        - **timeline_events**: 타임라인 이벤트 목록
    """
    # JSON body에서 flight_goal을 선택적으로 읽음 (Swagger/OpenAPI 비노출)
    raw_flight_goal = flight_goal_query
    raw_seat_class = None
    if request is not None:
        try:
            body = await request.json()
            if isinstance(body, dict):
                raw_flight_goal = body.get("flight_goal") or body.get("flightGoal")
                raw_seat_class = body.get("seat_class") or body.get("seatClass")
        except Exception:
            # body가 없거나 JSON이 아니면 무시
            pass

    flight_goal = _normalize_flight_goal(raw_flight_goal)
    # seat_class도 body로 들어오면 우선 적용 (기존 Query 호환 유지)
    if isinstance(raw_seat_class, str) and raw_seat_class.strip():
        seat_class = raw_seat_class.strip().upper()

    # 인증 확인: 우리 서비스 JWT 검증 (my-flights와 동일한 방식)
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        token_user_id = payload.get("sub")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
    
    if not token_user_id:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

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
        
    # 사용자 수면 패턴 조회
    user_sleep_pattern = None
    try:
        sleep_pattern_data = await UserService.get_sleep_pattern(uid=user_id)
        if sleep_pattern_data and sleep_pattern_data.get("sleepPatternStart") and sleep_pattern_data.get("sleepPatternEnd"):
            user_sleep_pattern = {
                "sleep_start": sleep_pattern_data["sleepPatternStart"],
                "sleep_end": sleep_pattern_data["sleepPatternEnd"]
            }
    except Exception as e:
        # 수면 패턴 조회 실패 시 무시하고 계속 진행
        pass
    
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
        segments=flight_segments if flight_segments else None,
        has_stopover=my_flight.hasStopover,
        user_sleep_pattern=user_sleep_pattern  # 사용자 수면 패턴 추가
    )
    
    # 타임라인 생성 서비스 호출
    return await flight_timeline_service.generate_flight_timeline(request)

