"""
비행 타임라인 생성 비즈니스 로직
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

from app.feature.wellness.flight_timeline_schemas import (
    FlightTimelineRequest,
    FlightTimelineResponse,
    TimelineEvent
)
from app.feature.llm import llm_service
from app.feature.llm.llm_schemas import LLMChatRequest


def calculate_duration_str(departure: datetime, arrival: datetime) -> str:
    """비행 시간을 'Xh Ym' 형식으로 계산"""
    duration = arrival - departure
    hours = int(duration.total_seconds() // 3600)
    minutes = int((duration.total_seconds() % 3600) // 60)
    return f"{hours}h {minutes}m"


def format_display_time(start: datetime, end: datetime) -> str:
    """시간을 'HH:MM - HH:MM' 형식으로 포맷"""
    return f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')}"


async def generate_flight_timeline(request: FlightTimelineRequest) -> FlightTimelineResponse:
    """
    LLM을 사용하여 비행 타임라인을 생성합니다.
    
    Args:
        request: 비행 타임라인 생성 요청
        
    Returns:
        Flight Timeline Response
    """
    # 총 비행 시간 계산
    total_duration = request.total_duration or calculate_duration_str(
        request.departure_time, 
        request.arrival_time
    )
    
    # LLM 프롬프트 구성
    prompt = f"""당신은 비행 경험 최적화 전문가입니다. 다음 비행 정보를 바탕으로 사용자의 목표에 맞는 최적의 타임라인을 생성해주세요.

**비행 정보:**
- 출발지: {request.origin}
- 도착지: {request.destination}
- 출발 시간: {request.departure_time.isoformat()}
- 도착 시간: {request.arrival_time.isoformat()}
- 총 비행 시간: {total_duration}
- 좌석 등급: {request.seat_class}
- 비행 목표: {request.flight_goal}

**비행 목표 설명:**
- SLEEP_FOCUS: 시차 적응을 위한 수면 집중
- WORK_FOCUS: 업무/생산성 집중
- ENTERTAINMENT: 휴식 및 엔터테인먼트 즐기기

**요청사항:**
사용자의 비행 목표({request.flight_goal})에 맞춰 타임라인을 생성하세요.

다음 JSON 형식으로 정확히 응답해주세요:

{{
  "recommendation_message": "BIMO가 '{request.flight_goal}'을 위한 플랜을 준비했어요. 자유롭게 수정하거나 삭제할 수 있어요.",
  "timeline_events": [
    {{
      "order": 1,
      "type": "TAKEOFF",
      "icon_type": "airplane_takeoff",
      "title": "이륙 및 안정",
      "description": "BIMO와 함께 스마트한 비행을 시작합니다.",
      "hours_from_departure": 0.0,
      "duration_hours": 2.0
    }},
    {{
      "order": 2,
      "type": "MEAL",
      "icon_type": "meal",
      "title": "예상 식사 시간",
      "description": "첫 번째 기내식이 제공될 예상 시간입니다.",
      "hours_from_departure": 2.0,
      "duration_hours": 1.0
    }},
    {{
      "order": 3,
      "type": "SLEEP",
      "icon_type": "moon",
      "title": "수면 시간",
      "description": "충분한 휴식을 취하세요.",
      "hours_from_departure": 3.0,
      "duration_hours": 5.0
    }},
    {{
      "order": 4,
      "type": "FREE_TIME",
      "icon_type": "play",
      "title": "자유 시간",
      "description": "자유롭게 시간을 활용하세요.",
      "hours_from_departure": 8.0,
      "duration_hours": 3.0
    }},
    {{
      "order": 5,
      "type": "LANDING",
      "icon_type": "airplane_landing",
      "title": "착륙 및 안정",
      "description": "BIMO와 함께 스마트한 비행을 마무리합니다.",
      "hours_from_departure": 11.0,
      "duration_hours": 1.0
    }}
  ]
}}

**중요 사항:**
1. timeline_events는 반드시 배열이어야 합니다
2. 각 이벤트는 hours_f rom_departure(출발 후 경과 시간)와 duration_hours(이벤트 지속 시간)을 포함해야 합니다
3. 이벤트 타입(type)은 다음 중 하나여야 합니다: TAKEOFF, MEAL, SLEEP, WORK, ENTERTAINMENT, FREE_TIME, LANDING
4. 첫 이벤트는 반드시 TAKEOFF, 마지막 이벤트는 반드시 LANDING이어야 합니다
5. 전체 이벤트 시간이 총 비행 시간({total_duration})을 초과하지 않아야 합니다
6. SLEEP_FOCUS면 수면 시간을 길게, WORK_FOCUS면 업무/집중 시간을 포함, ENTERTAINMENT면 엔터테인먼트 시간을 포함하세요
7. JSON 형식을 정확히 지켜주세요. 다른 텍스트 없이 JSON만 반환하세요.
"""

    system_instruction = (
        "You are a flight experience optimization expert. Generate optimal in-flight timelines "
        "based on user goals (sleep focus, work focus, or entertainment). "
        "Consider flight duration, seat class, and user preferences. "
        "IMPORTANT: Respond ONLY with valid JSON format, no additional text."
    )
    
    # LLM  호출
    llm_request = LLMChatRequest(
        prompt=prompt,
        system_instruction=system_instruction
    )
    
    llm_response = await llm_service.generate_chat_completion(llm_request)
    
    # LLM 응답 파싱
    try:
        # JSON 추출 (LLM이 추가 텍스트를 포함할 수 있으므로)
        json_str = llm_response.strip()
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()
        
        parsed_data = json.loads(json_str)
        
        # 타임라인 이벤트 생성
        timeline_events = []
        for event_data in parsed_data.get("timeline_events", []):
            # 시간 계산
            hours_from_departure = event_data.get("hours_from_departure", 0.0)
            duration_hours = event_data.get("duration_hours", 1.0)
            
            start_time = request.departure_time + timedelta(hours=hours_from_departure)
            end_time = start_time + timedelta(hours=duration_hours)
            
            timeline_events.append(
                TimelineEvent(
                    order=event_data.get("order"),
                    type=event_data.get("type"),
                    icon_type=event_data.get("icon_type"),
                    title=event_data.get("title"),
                    description=event_data.get("description"),
                    start_time=start_time.isoformat(),
                    end_time=end_time.isoformat(),
                    display_time=format_display_time(start_time, end_time)
                )
            )
        
        # 응답 생성
        return FlightTimelineResponse(
            flight_info={
                "origin": request.origin,
                "destination": request.destination,
                "total_duration": total_duration,
                "seat_class": request.seat_class,
                "flight_goal": request.flight_goal
            },
            recommendation_message=parsed_data.get(
                "recommendation_message",
                f"BIMO가 '{request.flight_goal}'을 위한 플랜을 준비했어요. 자유롭게 수정하거나 삭제할 수 있어요."
            ),
            timeline_events=timeline_events
        )
        
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        # LLM 응답 파싱 실패 시 기본 타임라인 생성
        print(f"LLM 응답 파싱 실패: {e}, 기본 타임라인 생성")
        return _generate_default_timeline(request, total_duration)


def _generate_default_timeline(
    request: FlightTimelineRequest, 
    total_duration: str
) -> FlightTimelineResponse:
    """기본 타임라인 생성 (LLM 실패 시 fallback)"""
    
    # 비행 시간 파싱
    duration_parts = total_duration.replace('h', '').replace('m', '').split()
    total_hours = float(duration_parts[0])
    if len(duration_parts) > 1:
        total_hours += float(duration_parts[1]) / 60
    
    events = []
    current_time = request.departure_time
    
    # 1. 이륙 및 안정 (첫 2시간)
    takeoff_duration = min(2.0, total_hours * 0.15)
    events.append({
        "order": 1,
        "type": "TAKEOFF",
        "icon_type": "airplane_takeoff",
        "title": "이륙 및 안정",
        "description": "BIM O와 함께 스마트한 비행을 시작합니다.",
        "start": current_time,
        "duration": takeoff_duration
    })
    current_time += timedelta(hours=takeoff_duration)
    
    # 2. 첫 번째 식사
    meal_duration = 1.0
    events.append({
        "order": 2,
        "type": "MEAL",
        "icon_type": "meal",
        "title": "예상 식사 시간",
        "description": "첫 번째 기내식이 제공될 예상 시간입니다.",
        "start": current_time,
        "duration": meal_duration
    })
    current_time += timedelta(hours=meal_duration)
    
    # 3. 메인 활동 (비행 목표에 따라)
    remaining_hours = total_hours - takeoff_duration - meal_duration - 2.0  # 착륙 시간 제외
    
    if request.flight_goal == "SLEEP_FOCUS":
        events.append({
            "order": 3,
            "type": "SLEEP",
            "icon_type": "moon",
            "title": "앵커 수면",
            "description": "시차 적응을 위한 핵심 수면 시간입니다. 안대를 착용하세요.",
            "start": current_time,
            "duration": remaining_hours * 0.7
        })
        current_time += timedelta(hours=remaining_hours * 0.7)
        
        events.append({
            "order": 4,
            "type": "FREE_TIME",
            "icon_type": "play",
            "title": "자유 시간",
            "description": "자유롭게 일정을 등록하실 수 있습니다.",
            "start": current_time,
            "duration": remaining_hours * 0.3
        })
        current_time += timedelta(hours=remaining_hours * 0.3)
        
    elif request.flight_goal == "WORK_FOCUS":
        events.append({
            "order": 3,
            "type": "WORK",
            "icon_type": "laptop",
            "title": "업무 시간",
            "description": "집중해서 업무를 처리할 시간입니다.",
            "start": current_time,
            "duration": remaining_hours * 0.6
        })
        current_time += timedelta(hours=remaining_hours * 0.6)
        
        events.append({
            "order": 4,
            "type": "FREE_TIME",
            "icon_type": "play",
            "title": "휴식 시간",
            "description": "가벼운 휴식을 취하세요.",
            "start": current_time,
            "duration": remaining_hours * 0.4
        })
        current_time += timedelta(hours=remaining_hours * 0.4)
        
    else:  # ENTERTAINMENT
        events.append({
            "order": 3,
            "type": "ENTERTAINMENT",
            "icon_type": "movie",
            "title": "엔터테인먼트",
            "description": "영화나 음악을 즐기세요.",
            "start": current_time,
            "duration": remaining_hours * 0.7
        })
        current_time += timedelta(hours=remaining_hours * 0.7)
        
        events.append({
            "order": 4,
            "type": "FREE_TIME",
            "icon_type": "play",
            "title": "자유 시간",
            "description": "자유롭게 시간을 활용하세요.",
            "start": current_time,
            "duration": remaining_hours * 0.3
        })
        current_time += timedelta(hours=remaining_hours * 0.3)
    
    # 5. 착륙 및 안정
    events.append({
        "order": 5,
        "type": "LANDING",
        "icon_type": "airplane_landing",
        "title": "착륙 및 안정",
        "description": "BIMO와 함께 스마트한 비행을 마무리합니다.",
        "start": current_time,
        "duration": 2.0
    })
    
    # TimelineEvent 객체로 변환
    timeline_events = []
    for event in events:
        start = event["start"]
        end = start + timedelta(hours=event["duration"])
        timeline_events.append(
            TimelineEvent(
                order=event["order"],
                type=event["type"],
                icon_type=event["icon_type"],
                title=event["title"],
                description=event["description"],
                start_time=start.isoformat(),
                end_time=end.isoformat(),
                display_time=format_display_time(start, end)
            )
        )
    
    return FlightTimelineResponse(
        flight_info={
            "origin": request.origin,
            "destination": request.destination,
            "total_duration": total_duration,
            "seat_class": request.seat_class,
            "flight_goal": request.flight_goal
        },
        recommendation_message=f"BIMO가 '{request.flight_goal}'을 위한 플랜을 준비했어요. 자유롭게 수정하거나 삭제할 수 있어요.",
        timeline_events=timeline_events
    )
