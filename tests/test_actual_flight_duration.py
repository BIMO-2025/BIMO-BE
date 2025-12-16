"""
다중 경유 항공편 순수 비행시간 계산 테스트 추가
"""

import pytest
from datetime import datetime, timezone
from app.feature.wellness.flight_timeline_schemas import FlightSegmentInfo
from app.feature.wellness.flight_timeline_service import _calculate_actual_flight_duration


def test_calculate_actual_flight_duration_single_segment():
    """1구간 (직항) 순수 비행시간 계산"""
    segments = [
        FlightSegmentInfo(
            origin="ICN",
            destination="JFK",
            departure_time=datetime(2025, 12, 25, 10, 0, tzinfo=timezone.utc),
            arrival_time=datetime(2025, 12, 25, 22, 30, tzinfo=timezone.utc),
            duration="12h 30m"
        )
    ]
    
    result = _calculate_actual_flight_duration(segments)
    assert result == "12h 30m"


def test_calculate_actual_flight_duration_two_segments():
    """2구간 (1회 경유) 순수 비행시간 계산"""
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
    
    # 순수 비행시간 = 3h 30m + 11h 0m = 14h 30m
    # 총 소요시간 = 16h 30m (경유 2시간 포함)
    result = _calculate_actual_flight_duration(segments)
    assert result == "14h 30m"


def test_calculate_actual_flight_duration_three_segments():
    """3구간 (2회 경유) 순수 비행시간 계산"""
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
    
    # 순수 비행시간 = 8h + 7h + 7h = 22h
    # 총 소요시간 = 31h (DXB 경유 7시간 + LHR 경유 2시간 포함)
    result = _calculate_actual_flight_duration(segments)
    assert result == "22h 0m"


def test_calculate_actual_flight_duration_with_minutes_only():
    """분 단위만 있는 경우"""
    segments = [
        FlightSegmentInfo(
            origin="GMP",
            destination="CJU",
            departure_time=datetime(2025, 12, 25, 10, 0, tzinfo=timezone.utc),
            arrival_time=datetime(2025, 12, 25, 11, 0, tzinfo=timezone.utc),
            duration="55m"
        )
    ]
    
    result = _calculate_actual_flight_duration(segments)
    assert result == "0h 55m"


def test_calculate_actual_flight_duration_empty_segments():
    """빈 segments 리스트"""
    result = _calculate_actual_flight_duration([])
    assert result == "0h 0m"
