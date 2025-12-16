"""
경유 항공편 타임라인 생성 테스트

pytest tests/test_flight_timeline_layover.py -v
"""

import pytest
from datetime import datetime, timezone
from app.feature.wellness.flight_timeline_schemas import (
    FlightTimelineRequest,
    FlightSegmentInfo,
    LayoverInfo
)
from app.feature.wellness.flight_timeline_service import (
    _calculate_layover_info,
    generate_flight_timeline
)


class TestLayoverCalculation:
    """경유 정보 계산 테스트"""

    def test_calculate_single_layover(self):
        """1회 경유 정보 계산 테스트"""
        segments = [
            FlightSegmentInfo(
                origin="ICN",
                destination="NRT",
                departure_time=datetime(2025, 12, 25, 10, 0, tzinfo=timezone.utc),
                arrival_time=datetime(2025, 12, 25, 13, 30, tzinfo=timezone.utc),
                duration="3h 30m"
            ),
            FlightSegmentInfo(
                origin="NRT",
                destination="JFK",
                departure_time=datetime(2025, 12, 25, 15, 30, tzinfo=timezone.utc),
                arrival_time=datetime(2025, 12, 26, 2, 30, tzinfo=timezone.utc),
                duration="11h 0m"
            )
        ]
        
        layovers = _calculate_layover_info(segments)
        
        assert len(layovers) == 1
        assert layovers[0].airport == "NRT"
        assert layovers[0].duration_hours == 2.0
        assert layovers[0].start_time == datetime(2025, 12, 25, 13, 30, tzinfo=timezone.utc)
        assert layovers[0].end_time == datetime(2025, 12, 25, 15, 30, tzinfo=timezone.utc)

    def test_calculate_multiple_layovers(self):
        """2회 경유 정보 계산 테스트"""
        segments = [
            FlightSegmentInfo(
                origin="ICN",
                destination="DXB",
                departure_time=datetime(2025, 12, 25, 10, 0, tzinfo=timezone.utc),
                arrival_time=datetime(2025, 12, 25, 18, 0, tzinfo=timezone.utc),
                duration="8h 0m"
            ),
            FlightSegmentInfo(
                origin="DXB",
                destination="LHR",
                departure_time=datetime(2025, 12, 26, 1, 0, tzinfo=timezone.utc),
                arrival_time=datetime(2025, 12, 26, 8, 0, tzinfo=timezone.utc),
                duration="7h 0m"
            ),
            FlightSegmentInfo(
                origin="LHR",
                destination="JFK",
                departure_time=datetime(2025, 12, 26, 10, 0, tzinfo=timezone.utc),
                arrival_time=datetime(2025, 12, 26, 17, 0, tzinfo=timezone.utc),
                duration="7h 0m"
            )
        ]
        
        layovers = _calculate_layover_info(segments)
        
        assert len(layovers) == 2
        assert layovers[0].airport == "DXB"
        assert layovers[0].duration_hours == 7.0
        assert layovers[1].airport == "LHR"
        assert layovers[1].duration_hours == 2.0


class TestFlightTimelineWithLayover:
    """경유 항공편 타임라인 생성 통합 테스트"""

    @pytest.mark.asyncio
    async def test_direct_flight_backward_compatibility(self):
        """직항 항공편 - 하위 호환성 테스트"""
        request = FlightTimelineRequest(
            origin="ICN",
            destination="JFK",
            departure_time=datetime(2025, 12, 25, 10, 0, tzinfo=timezone.utc),
            arrival_time=datetime(2025, 12, 25, 22, 30, tzinfo=timezone.utc),
            seat_class="ECONOMY",
            flight_goal="SLEEP_FOCUS",
            total_duration="12h 30m"
        )
        
        # 기존 방식대로 작동하는지 확인
        response = await generate_flight_timeline(request)
        
        assert response.timeline_events is not None
        assert len(response.timeline_events) > 0
        assert response.flight_info["origin"] == "ICN"
        assert response.flight_info["destination"] == "JFK"

    @pytest.mark.asyncio
    async def test_layover_flight_with_segments(self):
        """경유 항공편 - segments 제공 시 테스트"""
        segments = [
            FlightSegmentInfo(
                origin="ICN",
                destination="NRT",
                departure_time=datetime(2025, 12, 25, 10, 0, tzinfo=timezone.utc),
                arrival_time=datetime(2025, 12, 25, 13, 30, tzinfo=timezone.utc),
                duration="3h 30m"
            ),
            FlightSegmentInfo(
                origin="NRT",
                destination="JFK",
                departure_time=datetime(2025, 12, 25, 15, 30, tzinfo=timezone.utc),
                arrival_time=datetime(2025, 12, 26, 2, 30, tzinfo=timezone.utc),
                duration="11h 0m"
            )
        ]
        
        request = FlightTimelineRequest(
            origin="ICN",
            destination="JFK",
            departure_time=datetime(2025, 12, 25, 10, 0, tzinfo=timezone.utc),
            arrival_time=datetime(2025, 12, 26, 2, 30, tzinfo=timezone.utc),
            seat_class="ECONOMY",
            flight_goal="SLEEP_FOCUS",
            total_duration="16h 30m",
            segments=segments
        )
        
        response = await generate_flight_timeline(request)
        
        # 경유 정보가 반영되었는지 확인
        assert response.timeline_events is not None
        assert len(response.timeline_events) > 0
        
        # 프롬프트에 경유 정보가 포함되었는지는 LLM 응답으로 간접 확인
        # (실제로는 LLM이 LAYOVER 이벤트를 생성할 것으로 기대)
