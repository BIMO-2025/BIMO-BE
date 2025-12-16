"""
datetime_utils 유틸리티 함수 테스트
"""

import pytest
from datetime import datetime, timezone
from app.shared.datetime_utils import (
    parse_iso_datetime,
    parse_iso_duration,
    parse_duration_seconds,
)


class TestParseIsoDatetime:
    """parse_iso_datetime 함수 테스트"""
    
    def test_parse_iso_string_with_z(self):
        """Z timezone이 포함된 ISO 문자열 파싱"""
        result = parse_iso_datetime("2024-12-16T10:30:00Z")
        assert result.year == 2024
        assert result.month == 12
        assert result.day == 16
        assert result.hour == 10
        assert result.minute == 30
        assert result.second == 0
    
    def test_parse_iso_string_with_offset(self):
        """시간대 오프셋이 포함된 ISO 문자열 파싱"""
        result = parse_iso_datetime("2024-12-16T10:30:00+09:00")
        assert result.year == 2024
        assert result.month == 12
        assert result.day == 16
    
    def test_parse_datetime_object(self):
        """이미 datetime 객체인 경우 그대로 반환"""
        dt = datetime(2024, 12, 16, 10, 30)
        result = parse_iso_datetime(dt)
        assert result == dt
    
    def test_parse_invalid_type(self):
        """잘못된 타입 입력 시 TypeError 발생"""
        with pytest.raises(TypeError):
            parse_iso_datetime(123)
        
        with pytest.raises(TypeError):
            parse_iso_datetime(None)


class TestParseIsoDuration:
    """parse_iso_duration 함수 테스트"""
    
    def test_parse_hours_and_minutes(self):
        """시간과 분이 모두 있는 경우"""
        assert parse_iso_duration("PT14H30M") == "14H30M"
        assert parse_iso_duration("PT2H45M") == "2H45M"
    
    def test_parse_hours_only(self):
        """시간만 있는 경우"""
        assert parse_iso_duration("PT2H") == "2H"
        assert parse_iso_duration("PT14H") == "14H"
    
    def test_parse_minutes_only(self):
        """분만 있는 경우"""
        assert parse_iso_duration("PT45M") == "45M"
        assert parse_iso_duration("PT15M") == "15M"
    
    def test_parse_empty_string(self):
        """빈 문자열"""
        assert parse_iso_duration("") == "0M"
    
    def test_parse_none(self):
        """None 입력"""
        assert parse_iso_duration(None) == "0M"
    
    def test_parse_zero_duration(self):
        """0 시간 (PT0M 등)"""
        assert parse_iso_duration("PT0M") == "0M"


class TestParseDurationSeconds:
    """parse_duration_seconds 함수 테스트"""
    
    def test_parse_hours_and_minutes(self):
        """시간과 분 변환"""
        # 14시간 30분 = 52200초
        assert parse_duration_seconds(52200) == "14H30M"
        # 2시간 45분 = 9900초
        assert parse_duration_seconds(9900) == "2H45M"
    
    def test_parse_hours_only(self):
        """정확히 시간 단위"""
        # 2시간 = 7200초
        assert parse_duration_seconds(7200) == "2H"
    
    def test_parse_minutes_only(self):
        """분만 있는 경우"""
        # 45분 = 2700초
        assert parse_duration_seconds(2700) == "45M"
        # 15분 = 900초
        assert parse_duration_seconds(900) == "15M"
    
    def test_parse_zero(self):
        """0초"""
        assert parse_duration_seconds(0) == "0M"
    
    def test_parse_negative(self):
        """음수 (잘못된 입력)"""
        assert parse_duration_seconds(-100) == "0M"
    
    def test_parse_none(self):
        """None 입력"""
        assert parse_duration_seconds(None) == "0M"
