"""
시차적응 및 피로도 관리 관련 스키마
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class FlightSegment(BaseModel):
    """비행 구간 정보"""
    departure_airport: str = Field(..., description="출발 공항 코드 (예: ICN)")
    arrival_airport: str = Field(..., description="도착 공항 코드 (예: JFK)")
    departure_time: datetime = Field(..., description="출발 시간 (ISO 8601)")
    arrival_time: datetime = Field(..., description="도착 시간 (ISO 8601)")
    flight_duration_hours: Optional[float] = Field(None, description="비행 시간 (시간 단위)")
    
    model_config = ConfigDict(from_attributes=True)


class JetLagPlanRequest(BaseModel):
    """시차적응 계획 요청 스키마"""
    flight_segments: List[FlightSegment] = Field(..., min_length=1, description="비행 구간 목록")
    destination_timezone: str = Field(..., description="도착지 시간대 (예: America/New_York)")
    origin_timezone: Optional[str] = Field(None, description="출발지 시간대 (예: Asia/Seoul, 선택사항)")
    user_sleep_pattern_start: Optional[str] = Field(None, description="사용자 평소 수면 시작 시간 (HH:MM 형식)")
    user_sleep_pattern_end: Optional[str] = Field(None, description="사용자 평소 수면 종료 시간 (HH:MM 형식)")
    trip_duration_days: Optional[int] = Field(None, ge=1, description="여행 기간 (일 단위)")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "flight_segments": [
                    {
                        "departure_airport": "ICN",
                        "arrival_airport": "JFK",
                        "departure_time": "2025-12-25T13:45:00Z",
                        "arrival_time": "2025-12-25T18:20:00Z",
                        "flight_duration_hours": 14.5
                    }
                ],
                "destination_timezone": "America/New_York",
                "origin_timezone": "Asia/Seoul",
                "user_sleep_pattern_start": "23:00",
                "user_sleep_pattern_end": "07:00",
                "trip_duration_days": 7
            }
        }
    )


class DailySchedule(BaseModel):
    """일별 일정"""
    date: str = Field(..., description="날짜 (YYYY-MM-DD)")
    day_number: int = Field(..., description="여행 시작일 기준 일수 (0부터 시작)")
    local_timezone: str = Field(..., description="현재 위치의 시간대")
    sleep_window: str = Field(..., description="권장 수면 시간대 (예: 22:00 - 06:00)")
    meal_times: List[str] = Field(..., description="권장 식사 시간 (HH:MM 형식)")
    activities: List[str] = Field(..., description="권장 활동 목록")
    notes: str = Field(..., description="특별 주의사항")
    
    model_config = ConfigDict(from_attributes=True)


class JetLagPlanResponse(BaseModel):
    """시차적응 계획 응답 스키마"""
    origin_timezone: str
    destination_timezone: str
    time_difference_hours: int = Field(..., description="시차 (시간 단위)")
    total_flight_duration_hours: float = Field(..., description="총 비행 시간")
    daily_schedules: List[DailySchedule] = Field(..., description="일별 일정")
    general_recommendations: List[str] = Field(..., description="일반적인 권장사항")
    pre_flight_tips: List[str] = Field(..., description="출발 전 팁")
    post_arrival_tips: List[str] = Field(..., description="도착 후 팁")
    algorithm_explanation: str = Field(..., description="LLM이 생성한 알고리즘 설명")
    
    model_config = ConfigDict(from_attributes=True)


