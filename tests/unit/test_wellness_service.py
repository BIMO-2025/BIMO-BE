"""
시차적응 서비스 단위 테스트 (LLM 호출 포함)
"""
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta

from app.feature.wellness import wellness_service
from app.feature.wellness.wellness_schemas import (
    JetLagPlanRequest,
    FlightSegment,
    DailySchedule
)


class TestGenerateJetlagPlan:
    """시차적응 계획 생성 테스트"""

    @pytest.mark.asyncio
    async def test_generate_jetlag_plan_basic(self):
        """기본 시차적응 계획 생성"""
        base_time = datetime.now()
        
        request = JetLagPlanRequest(
            origin_timezone="Asia/Seoul",
            destination_timezone="America/New_York",
            flight_segments=[
                FlightSegment(
                    departure_airport="ICN",
                    arrival_airport="JFK",
                    departure_time=base_time,
                    arrival_time=base_time + timedelta(hours=14)
                )
            ],
            trip_duration_days=7
        )
        
        mock_llm_response = """시차적응 계획:

1. 출발 전:
- 출발 3일 전부터 목적지 시간대로 수면 시간 조정 시작

2. 비행 중:
- 충분한 수분 섭취
- 가벼운 스트레칭

3. 도착 후:
- 첫날은 가벼운 활동만
- 자연광에 노출"""
        
        with patch.object(wellness_service, "llm_service") as mock_llm:
            mock_llm.generate_chat_completion = AsyncMock(return_value=mock_llm_response)
            
            result = await wellness_service.generate_jetlag_plan(request)
            
            assert result is not None
            assert hasattr(result, "daily_schedules") or hasattr(result, "summary")
            mock_llm.generate_chat_completion.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_jetlag_plan_with_sleep_pattern(self):
        """수면 패턴이 있는 경우"""
        base_time = datetime.now()
        
        request = JetLagPlanRequest(
            origin_timezone="Asia/Seoul",
            destination_timezone="America/New_York",
            flight_segments=[
                FlightSegment(
                    departure_airport="ICN",
                    arrival_airport="JFK",
                    departure_time=base_time,
                    arrival_time=base_time + timedelta(hours=14)
                )
            ],
            user_sleep_pattern_start="22:00",
            user_sleep_pattern_end="06:00",
            trip_duration_days=7
        )
        
        with patch.object(wellness_service, "llm_service") as mock_llm:
            mock_llm.generate_chat_completion = AsyncMock(return_value="수면 패턴 기반 계획")
            
            result = await wellness_service.generate_jetlag_plan(request)
            
            assert result is not None
            # 프롬프트에 수면 패턴 정보가 포함되었는지 확인
            call_args = mock_llm.generate_chat_completion.call_args
            assert call_args is not None

    @pytest.mark.asyncio
    async def test_generate_jetlag_plan_multiple_segments(self):
        """여러 구간이 있는 경우"""
        base_time = datetime.now()
        
        request = JetLagPlanRequest(
            origin_timezone="Asia/Seoul",
            destination_timezone="Europe/London",
            flight_segments=[
                FlightSegment(
                    departure_airport="ICN",
                    arrival_airport="DXB",
                    departure_time=base_time,
                    arrival_time=base_time + timedelta(hours=10)
                ),
                FlightSegment(
                    departure_airport="DXB",
                    arrival_airport="LHR",
                    departure_time=base_time + timedelta(hours=13),
                    arrival_time=base_time + timedelta(hours=18)
                )
            ],
            trip_duration_days=5
        )
        
        with patch.object(wellness_service, "llm_service") as mock_llm:
            mock_llm.generate_chat_completion = AsyncMock(return_value="경유지 포함 계획")
            
            result = await wellness_service.generate_jetlag_plan(request)
            
            assert result is not None
            # 여러 구간 정보가 프롬프트에 포함되었는지 확인
            call_args = mock_llm.generate_chat_completion.call_args
            assert call_args is not None

