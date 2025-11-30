"""
시차적응 및 피로도 관리 API 라우터
"""

from fastapi import APIRouter

from app.feature.wellness import wellness_schemas, wellness_service

router = APIRouter(
    prefix="/wellness",
    tags=["Wellness"],
    responses={404: {"description": "Not found"}},
)


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


