"""
비행 타임라인 관련 스키마 추가
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


# 기존 스키마들...
# (wellness_schemas.py의 기존 내용 유지)


class FlightSegmentInfo(BaseModel):
    """비행 구간 정보"""
    origin: str = Field(..., description="구간 출발 공항 코드 (예: ICN)")
    destination: str = Field(..., description="구간 도착 공항 코드 (예: NRT)")
    departure_time: datetime = Field(..., description="구간 출발 시간")
    arrival_time: datetime = Field(..., description="구간 도착 시간")
    duration: str = Field(..., description="구간 비행 시간 (예: 3h 30m)")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "origin": "ICN",
                "destination": "NRT",
                "departure_time": "2025-12-25T10:00:00Z",
                "arrival_time": "2025-12-25T13:30:00Z",
                "duration": "3h 30m"
            }
        }
    )


class LayoverInfo(BaseModel):
    """경유 대기 정보"""
    airport: str = Field(..., description="경유 공항 코드 (예: NRT)")
    duration_hours: float = Field(..., description="대기 시간 (시간 단위)")
    start_time: datetime = Field(..., description="경유 시작 시간 (도착 시간)")
    end_time: datetime = Field(..., description="경유 종료 시간 (다음 출발 시간)")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "airport": "NRT",
                "duration_hours": 2.0,
                "start_time": "2025-12-25T13:30:00Z",
                "end_time": "2025-12-25T15:30:00Z"
            }
        }
    )


class TimelineEvent(BaseModel):
    """타임라인 이벤트"""
    order: int = Field(..., description="순서")
    type: str = Field(..., description="이벤트 타입 (TAKEOFF, MEAL, SLEEP, WORK, ENTERTAINMENT, FREE_TIME, LAYOVER, CONNECTION, LANDING 등)")
    icon_type: str = Field(..., description="프론트엔드 아이콘 타입")
    title: str = Field(..., description="이벤트 제목")
    description: str = Field(..., description="이벤트 설명")
    start_time: str = Field(..., description="시작 시간 (ISO 8601)")
    end_time: str = Field(..., description="종료 시간 (ISO 8601)")
    display_time: str = Field(..., description="표시용 시간 (HH:MM - HH:MM)")
    
    model_config = ConfigDict(from_attributes=True)


class FlightTimelineRequest(BaseModel):
    """비행 타임라인 생성 요청"""
    # 기존 필드 (하위 호환성 유지)
    origin: str = Field(..., description="출발 공항 코드 (예: DXB)")
    destination: str = Field(..., description="도착 공항 코드 (예: ICN)")
    departure_time: datetime = Field(..., description="출발 시간")
    arrival_time: datetime = Field(..., description="도착 시간")
    seat_class: str = Field(..., description="좌석 등급 (ECONOMY, BUSINESS, FIRST 등)")
    flight_goal: str = Field(..., description="비행 목표 (SLEEP_FOCUS, WORK_FOCUS, ENTERTAINMENT 등)")
    total_duration: Optional[str] = Field(None, description="총 비행 시간 (예: 9h 30m)")
    
    # 경유 항공편 처리를 위한 새로운 필드 (옵션)
    segments: Optional[List[FlightSegmentInfo]] = Field(None, description="비행 구간 목록 (경유편의 경우)")
    layovers: Optional[List[LayoverInfo]] = Field(None, description="경유 대기 정보 (자동 계산되거나 직접 제공)")
    has_stopover: Optional[bool] = Field(None, description="경유 여부 (segments로부터 자동 판단)")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "origin": "DXB",
                "destination": "ICN",
                "departure_time": "2025-11-25T09:00:00",
                "arrival_time": "2025-11-25T21:00:00",
                "seat_class": "ECONOMY",
                "flight_goal": "SLEEP_FOCUS",
                "total_duration": "9h 30m"
            }
        }
    )


class FlightTimelineResponse(BaseModel):
    """비행 타임라인 응답"""
    flight_info: dict = Field(..., description="비행 정보")
    recommendation_message: str = Field(..., description="추천 메시지")
    timeline_events: List[TimelineEvent] = Field(..., description="타임라인 이벤트 목록")
    
    model_config = ConfigDict(from_attributes=True)
