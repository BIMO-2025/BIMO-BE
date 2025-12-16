"""
웰니스 및 비행 타임라인 관련 비즈니스 로직
"""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from app.feature.wellness.flight_timeline_schemas import (
    FlightTimelineRequest,
    FlightTimelineResponse,
    TimelineEvent,
    FlightSegmentInfo,
    LayoverInfo
)
from app.feature.llm.llm_service import LLMService
from app.feature.llm.llm_schemas import LLMChatRequest
from app.shared.datetime_utils import parse_duration_seconds

# 로거 설정
logger = logging.getLogger(__name__)


class WellnessService:
    """웰니스 및 타임라인 관련 비즈니스 로직을 처리하는 서비스 클래스"""

    def __init__(self, llm_service: LLMService):
        """
        WellnessService 초기화
        
        Args:
            llm_service: LLM 서비스 인스턴스
        """
        self.llm_service = llm_service

    def calculate_duration_str(self, departure: datetime, arrival: datetime) -> str:
        """비행 시간을 'Xh Ym' 형식으로 계산"""
        duration = arrival - departure
        return parse_duration_seconds(int(duration.total_seconds()))

    def format_display_time(self, start: datetime, end: datetime) -> str:
        """시간을 'HH:MM - HH:MM' 형식으로 포맷"""
        return f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')}"

    def _calculate_layover_info(self, segments: List[FlightSegmentInfo]) -> List[LayoverInfo]:
        """구간 정보로부터 경유 대기 정보 계산"""
        layovers = []
        for i in range(len(segments) - 1):
            current_arrival = segments[i].arrival_time
            next_departure = segments[i + 1].departure_time
            duration_hours = (next_departure - current_arrival).total_seconds() / 3600
            
            layovers.append(LayoverInfo(
                airport=segments[i].destination,
                duration_hours=duration_hours,
                start_time=current_arrival,
                end_time=next_departure
            ))
        return layovers

    def _calculate_actual_flight_duration(self, segments: List[FlightSegmentInfo]) -> str:
        """구간별 비행 시간을 합산하여 순수 비행 시간 계산 (경유 대기 시간 제외)"""
        if not segments:
            return "0h 0m"
        
        total_seconds = 0
        for segment in segments:
            # duration 파싱 (예: "3h 30m" -> 3.5시간)
            duration_str = segment.duration.lower()
            hours = 0
            minutes = 0
            
            if 'h' in duration_str:
                parts = duration_str.split('h')
                hours = int(parts[0].strip())
                if len(parts) > 1 and 'm' in parts[1]:
                    minutes = int(parts[1].replace('m', '').strip())
            elif 'm' in duration_str:
                minutes = int(duration_str.replace('m', '').strip())
            
            total_seconds += hours * 3600 + minutes * 60
        
        return parse_duration_seconds(int(total_seconds))

    async def generate_flight_timeline(self, request: FlightTimelineRequest) -> FlightTimelineResponse:
        """
        LLM을 사용하여 비행 타임라인을 생성합니다.
        
        Args:
            request: 비행 타임라인 생성 요청
            
        Returns:
            Flight Timeline Response
        """
        # 총 소요 시간 계산 (출발~도착, 경유 대기 시간 포함)
        total_journey_time = self.calculate_duration_str(
            request.departure_time, 
            request.arrival_time
        )
        
        # 경유 정보 처리
        segments = request.segments
        layovers = request.layovers
        has_stopover = request.has_stopover
        
        # segments가 제공되면 layovers 자동 계산
        if segments and len(segments) > 1:
            has_stopover = True
            if not layovers:
                layovers = self._calculate_layover_info(segments)
        elif segments and len(segments) == 1:
            has_stopover = False
        
        # 순수 비행 시간 계산 (경유 대기 시간 제외)
        actual_flight_duration = None
        if segments:
            actual_flight_duration = self._calculate_actual_flight_duration(segments)
        
        # total_duration: 프롬프트에 표시할 시간
        # - segments 있으면: 순수 비행 시간
        # - segments 없으면: 전체 여정 시간 (기존 동작)
        total_duration = actual_flight_duration or request.total_duration or total_journey_time
        
        # 경유 정보 프롬프트 생성
        segments_info = ""
        if segments and len(segments) > 0:
            segments_info = "\n\n**비행 구간 정보:**\n"
            for i, seg in enumerate(segments, 1):
                segments_info += f"""구간 {i}: {seg.origin} → {seg.destination}
- 출발: {seg.departure_time.strftime('%Y-%m-%d %H:%M')}
- 도착: {seg.arrival_time.strftime('%Y-%m-%d %H:%M')}
- 비행 시간: {seg.duration}

"""
        
        layovers_info = ""
        if layovers and len(layovers) > 0:
            layovers_info = "**경유 대기 정보:**\n"
            for i, layover in enumerate(layovers, 1):
                layovers_info += f"""경유지 {i}: {layover.airport}
- 대기 시간: {layover.duration_hours:.1f}시간
- {layover.start_time.strftime('%Y-%m-%d %H:%M')} ~ {layover.end_time.strftime('%Y-%m-%d %H:%M')}

"""
        
        # LLM 프롬프트 구성
        prompt = f"""당신은 Harvard Medical School의 Timeshifter 연구를 기반으로 한 비행 경험 최적화 전문가입니다. 
다음 비행 정보를 바탕으로 사용자의 목표에 맞는 최적의 타임라인을 생성해주세요.

**비행 정보:**
- 출발지: {request.origin}
- 도착지: {request.destination}
- 출발 시간: {request.departure_time.isoformat()}
- 도착 시간: {request.arrival_time.isoformat()}
- 총 소요 시간: {total_journey_time} (출발부터 도착까지)
- 순수 비행 시간: {total_duration} (경유 대기 시간 제외)
- 좌석 등급: {request.seat_class}
- 비행 목표: {request.flight_goal}
{segments_info}{layovers_info}
**비행 목표 설명:**
- SLEEP_FOCUS: 시차 적응을 위한 수면 집중
- WORK_FOCUS: 업무/생산성 집중
- ENTERTAINMENT: 휴식 및 엔터테인먼트 즐기기

**과학적 근거 (Timeshifter 연구):**
1. **빛 노출 (가장 중요!)**: 생체시계(Circadian Rhythm) 조절의 핵심
   - 동쪽 이동: 오전 빛 노출 권장 (+), 저녁 빛 차단 권장 (-)
   - 서쪽 이동: 저녁 빛 노출 권장 (+), 오전 빛 차단 권장 (-)
   
2. **Phase Response Curve (PRC)**: 빛 노출 타이밍에 따라 생체시계가 앞당겨지거나 늦춰짐
   
3. **수면 스케줄**: 목적지 시간대에 맞춘 수면으로 시차 적응 가속화
   
4. **구간별 전략**: 경유지에서도 최종 목적지 시간대 기준으로 조절

**사용자 생활패턴:**
{f"- 평소 수면 시간: {request.user_sleep_pattern['sleep_start']} ~ {request.user_sleep_pattern['sleep_end']}" if request.user_sleep_pattern and request.user_sleep_pattern.get('sleep_start') and request.user_sleep_pattern.get('sleep_end') else "- 정보 없음 (일반적인 수면 패턴 가정)"}
{"- 사용자의 평소 수면 패턴을 고려하여 기내 수면 시간을 조정하세요" if request.user_sleep_pattern and request.user_sleep_pattern.get('sleep_start') else ""}
{"- 사용자가 평소 늦게 자는 편이면 비행 초반 수면을 권장하고, 일찍 자는 편이면 비행 후반 수면을 권장하세요" if request.user_sleep_pattern and request.user_sleep_pattern.get('sleep_start') else ""}

**경유 시간별 권장사항:**
- 2시간 미만: 라운지 휴식, 가벼운 스트레칭
- 2-6시간: 목적지 시간대에 따라 수면/활동 조절, 샤워 시설 활용
- 6시간 이상: 공항 호텔 또는 수면실 이용, 본격적인 휴식
- 24시간 이상(스톱오버): 현지 활동, 야외 햇빛 노출로 시차 적응 시작

**요청사항:**
사용자의 비행 목표({request.flight_goal})와 경유 정보를 고려하여 타임라인을 생성하세요.

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
2. 각 이벤트는 hours_from_departure(출발 후 경과 시간)와 duration_hours(이벤트 지속 시간)을 포함해야 합니다
3. 이벤트 타입(type)은 다음 중 하나여야 합니다: 
   - TAKEOFF (이륙), MEAL (식사), SLEEP (수면), WORK (업무), ENTERTAINMENT (엔터테인먼트)
   - FREE_TIME (자유 시간), LAYOVER (경유 대기), CONNECTION (환승), LANDING (착륙)
4. 첫 이벤트는 반드시 TAKEOFF, 마지막 이벤트는 반드시 LANDING이어야 합니다
5. 경유 항공편의 경우:
   - 각 구간별로 TAKEOFF/LANDING 대신 구간 1 비행/구간 2 비행으로 표현
   - LAYOVER 또는 CONNECTION 이벤트를 경유 대기 시간에 맞춰 배치
   - 경유 시간에 따라 적절한 활동 권장 (라운지, 수면, 샤워 등)
6. **이벤트 배치 기준:**
   - 경유편: 순수 비행 시간({total_duration})만 고려하여 이벤트 배치
   - 경유 대기 시간은 LAYOVER 이벤트로 별도 표현
   - 전체 타임라인 = 비행 이벤트 + 경유 이벤트
7. SLEEP_FOCUS면 수면 시간을 길게, WORK_FOCUS면 업무/집중 시간을 포함, ENTERTAINMENT면 엔터테인먼트 시간을 포함하세요
8. 시차 적응을 위해 빛 노출/차단 권장사항을 description에 포함하세요
9. JSON 형식을 정확히 지켜주세요. 다른 텍스트 없이 JSON만 반환하세요.
"""

        system_instruction = (
            "You are a flight experience optimization expert. Generate optimal in-flight timelines "
            "based on user goals (sleep focus, work focus, or entertainment). "
            "Consider flight duration, seat class, and user preferences. "
            "IMPORTANT: Respond ONLY with valid JSON format, no additional text."
        )
        
        # LLM 호출
        llm_request = LLMChatRequest(
            prompt=prompt,
            system_instruction=system_instruction
        )
        
        llm_response = await self.llm_service.generate_chat_completion(llm_request)
        
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
                        display_time=self.format_display_time(start_time, end_time)
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
            logger.error(f"LLM 응답 파싱 실패: {e}, 기본 타임라인 생성")
            return self._generate_default_timeline(request, total_duration)

    def _generate_default_timeline(
        self,
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
            "description": "BIMO와 함께 스마트한 비행을 시작합니다.",
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
                    display_time=self.format_display_time(start, end)
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
