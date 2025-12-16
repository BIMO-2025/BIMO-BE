"""
[Deprecated] 비행 타임라인 생성 서비스
이 모듈은 app.feature.wellness.wellness_service 로 대체되었습니다.
하위 호환성을 위해 당분간 유지되지만, 곧 삭제될 예정입니다.
"""

from app.feature.wellness.wellness_service import WellnessService
from app.feature.wellness.flight_timeline_schemas import FlightTimelineRequest, FlightTimelineResponse
from app.core.deps import get_llm_service

# ============================================
# 하위 호환성을 위한 레거시 함수
# ============================================

async def generate_flight_timeline(request: FlightTimelineRequest) -> FlightTimelineResponse:
    """
    [레거시 함수] 비행 타임라인 생성
    
    Deprecated: WellnessService.generate_flight_timeline 사용을 권장합니다.
    """
    llm_service = get_llm_service()
    service = WellnessService(llm_service=llm_service)
    return await service.generate_flight_timeline(request)
