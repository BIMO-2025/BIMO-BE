"""
비행 타임라인 관련 스키마
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Literal, Optional
from datetime import datetime

# 타임라인 아이템 타입
TimelineItemType = Literal[
    "TAKEOFF",      # 이륙 및 안정
    "LANDING",      # 착륙 및 안정  
    "MEAL",         # 식사 시간
    "SLEEP",        # 수면 시간
    "FREE_TIME",    # 자유 시간
    "ACTIVITY"      # 기타 활동
]


class TimelineItemSchema(BaseModel):
    """
    타임라인 개별 아이템 스키마
    """
    type: TimelineItemType = Field(..., description="타임라인 아이템 타입")
    title: str = Field(..., description="타임라인 아이템 제목 (예: '이륙 및 안정', '예상 적극 식사')")
    start_time: str = Field(..., description="시작 시간 (ISO 8601 형식 또는 HH:MM)")
    end_time: str = Field(..., description="종료 시간 (ISO 8601 형식 또는 HH:MM)")
    description: Optional[str] = Field(None, description="상세 설명")
    icon: Optional[str] = Field(None, description="아이콘 이모지 (예: '✈️', '☁️', '🌙')")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "TAKEOFF",
                "title": "이륙 및 안정",
                "start_time": "09:00",
                "end_time": "11:00",
                "description": "BIMO와 함께 스트레칭 바쁘를 시작합니다.",
                "icon": "✈️"
            }
        }
    )


class FlightTimelineRequest(BaseModel):
    """
    비행 타임라인 생성 요청 스키마
    """
    flight_id: str = Field(..., description="비행 기록 ID (MyFlight ID)")
    user_id: str = Field(..., description="사용자 ID")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "flight_id": "flight_123",
                "user_id": "user_456"
            }
        }
    )


class FlightTimelineResponse(BaseModel):
    """
    비행 타임라인 응답 스키마
    """
    flight_id: str = Field(..., description="비행 기록 ID")
    
    # 비행편 기본 정보
    departure_airport: str = Field(..., description="출발 공항 코드 (예: DXB)")
    departure_airport_name: str = Field(..., description="출발 공항 이름 (예: 두바이)")
    arrival_airport: str = Field(..., description="도착 공항 코드 (예: ICN)")
    arrival_airport_name: str = Field(..., description="도착 공항 이름 (예: 인천)")
    
    departure_time: datetime = Field(..., description="출발 시간")
    arrival_time: datetime = Field(..., description="도착 시간")
    
    flight_date: str = Field(..., description="비행 날짜 (YYYY.MM.DD 형식)")
    day_of_week: str = Field(..., description="요일 (예: '토')")
    total_duration: str = Field(..., description="총 비행 시간 (예: '14h 15m')")
    
    # 항공편 정보
    airline_code: str = Field(..., description="항공사 코드 (예: 'KE')")
    airline_name: Optional[str] = Field(None, description="항공사 이름 (예: '대한항공')")
    flight_number: str = Field(..., description="항공편명 (예: 'KE123')")
    
    # 경유 정보
    has_stopover: bool = Field(False, description="경유 여부")
    stopover_count: int = Field(0, description="경유 횟수")
    
    # 타임라인 아이템들
    timeline_items: List[TimelineItemSchema] = Field(..., description="타임라인 아이템 목록")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "flight_id": "flight_123",
                "departure_airport": "DXB",
                "departure_airport_name": "두바이",
                "arrival_airport": "ICN",
                "arrival_airport_name": "인천",
                "departure_time": "2025-11-25T09:00:00Z",
                "arrival_time": "2025-11-25T23:15:00Z",
                "flight_date": "2025.11.25",
                "day_of_week": "토",
                "total_duration": "14h 15m",
                "airline_code": "KE",
                "airline_name": "대한항공",
                "flight_number": "KE123",
                "has_stopover": False,
                "stopover_count": 0,
                "timeline_items": [
                    {
                        "type": "TAKEOFF",
                        "title": "이륙 및 안정",
                        "start_time": "09:00",
                        "end_time": "11:00",
                        "description": "BIMO와 함께 스트레칭 바쁘를 시작합니다.",
                        "icon": "✈️"
                    },
                    {
                        "type": "MEAL",
                        "title": "예상 적극 식사",
                        "start_time": "11:00",
                        "end_time": "12:00",
                        "description": "첫 번째 기내식이 제공될 예정입니다.",
                        "icon": "☁️"
                    },
                    {
                        "type": "SLEEP",
                        "title": "예상 수면",
                        "start_time": "12:00",
                        "end_time": "17:00",
                        "description": "시차 적응을 위한 최적 수면 시간입니다.",
                        "icon": "🌙"
                    }
                ]
            }
        }
    )
