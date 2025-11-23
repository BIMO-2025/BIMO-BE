"""
시차적응(Wellness) 모듈 단위 테스트
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from app.feature.wellness.wellness_service import (
    calculate_time_difference,
    calculate_total_flight_duration,
)
from app.feature.wellness.wellness_schemas import FlightSegment


class TestTimeDifference:
    """시차 계산 테스트"""

    def test_calculate_time_difference_same_timezone(self):
        """같은 시간대"""
        diff = calculate_time_difference("Asia/Seoul", "Asia/Seoul")
        assert diff == 0

    def test_calculate_time_difference_seoul_to_ny(self):
        """서울에서 뉴욕 (대략 -13시간)"""
        diff = calculate_time_difference("Asia/Seoul", "America/New_York")
        # 실제 시차는 계절에 따라 다르지만, 대략 -13 ~ -14시간
        assert diff < 0
        assert abs(diff) >= 12

    def test_calculate_time_difference_seoul_to_tokyo(self):
        """서울에서 도쿄 (대략 +0시간, 거의 같음)"""
        diff = calculate_time_difference("Asia/Seoul", "Asia/Tokyo")
        # 실제로는 거의 같지만 약간의 차이가 있을 수 있음
        assert abs(diff) <= 1

    def test_calculate_time_difference_invalid_timezone(self):
        """유효하지 않은 시간대"""
        diff = calculate_time_difference("Invalid/Timezone", "Asia/Seoul")
        # 예외 처리로 0 반환
        assert diff == 0


class TestFlightDuration:
    """비행 시간 계산 테스트"""

    def test_calculate_total_flight_duration_single_segment(self):
        """단일 구간"""
        departure = datetime.now()
        arrival = departure + timedelta(hours=5)
        
        segments = [
            FlightSegment(
                departure_airport="ICN",
                arrival_airport="NRT",
                departure_time=departure,
                arrival_time=arrival
            )
        ]
        
        duration = calculate_total_flight_duration(segments)
        assert duration == pytest.approx(5.0, abs=0.1)

    def test_calculate_total_flight_duration_multiple_segments(self):
        """여러 구간"""
        base_time = datetime.now()
        
        segments = [
            FlightSegment(
                departure_airport="ICN",
                arrival_airport="NRT",
                departure_time=base_time,
                arrival_time=base_time + timedelta(hours=2)
            ),
            FlightSegment(
                departure_airport="NRT",
                arrival_airport="JFK",
                departure_time=base_time + timedelta(hours=3),
                arrival_time=base_time + timedelta(hours=13)
            )
        ]
        
        duration = calculate_total_flight_duration(segments)
        # 첫 구간: 2시간, 두 번째 구간: 10시간 = 총 12시간
        assert duration == pytest.approx(12.0, abs=0.1)

    def test_calculate_total_flight_duration_empty_list(self):
        """빈 구간 리스트"""
        duration = calculate_total_flight_duration([])
        assert duration == 0.0

    def test_calculate_total_flight_duration_with_layover(self):
        """경유지가 있는 경우"""
        base_time = datetime.now()
        
        segments = [
            FlightSegment(
                departure_airport="ICN",
                arrival_airport="DXB",
                departure_time=base_time,
                arrival_time=base_time + timedelta(hours=10)
            ),
            FlightSegment(
                departure_airport="DXB",
                arrival_airport="LHR",
                departure_time=base_time + timedelta(hours=13),  # 3시간 경유
                arrival_time=base_time + timedelta(hours=18)
            )
        ]
        
        duration = calculate_total_flight_duration(segments)
        # 첫 구간: 10시간, 두 번째 구간: 5시간 = 총 15시간 (경유 시간 제외)
        assert duration == pytest.approx(15.0, abs=0.1)

