"""
시차적응 및 피로도 관리 비즈니스 로직
"""

from typing import List
import pytz
import re
from datetime import datetime, timedelta

from app.feature.wellness.wellness_schemas import (
    JetLagPlanRequest,
    JetLagPlanResponse,
    DailySchedule,
    FlightSegment
)
from app.feature.llm import llm_service
from app.feature.llm.llm_schemas import LLMChatRequest


def calculate_time_difference(origin_tz: str, dest_tz: str) -> int:
    """
    두 시간대 간의 시차를 계산합니다.
    
    Args:
        origin_tz: 출발지 시간대
        dest_tz: 도착지 시간대
        
    Returns:
        시차 (시간 단위)
    """
    try:
        origin_timezone = pytz.timezone(origin_tz)
        dest_timezone = pytz.timezone(dest_tz)
        
        # 현재 시간 기준으로 시차 계산
        now = datetime.now(origin_timezone)
        origin_offset = now.utcoffset().total_seconds() / 3600
        dest_offset = now.astimezone(dest_timezone).utcoffset().total_seconds() / 3600
        
        return int(dest_offset - origin_offset)
    except Exception:
        # 시간대 계산 실패 시 기본값 반환
        return 0


def calculate_total_flight_duration(segments: List[FlightSegment]) -> float:
    """
    총 비행 시간을 계산합니다.
    
    Args:
        segments: 비행 구간 목록
        
    Returns:
        총 비행 시간 (시간 단위)
    """
    total = 0.0
    for segment in segments:
        if segment.flight_duration_hours:
            total += segment.flight_duration_hours
        else:
            # duration이 없으면 도착 시간 - 출발 시간으로 계산
            duration = (segment.arrival_time - segment.departure_time).total_seconds() / 3600
            total += duration
    return total


async def generate_jetlag_plan(request: JetLagPlanRequest) -> JetLagPlanResponse:
    """
    LLM을 사용하여 시차적응 계획을 생성합니다.
    
    Args:
        request: 시차적응 계획 요청
        
    Returns:
        시차적응 계획 응답
    """
    # 1. 기본 정보 계산
    origin_tz = request.origin_timezone or "UTC"
    dest_tz = request.destination_timezone
    time_diff = calculate_time_difference(origin_tz, dest_tz)
    total_duration = calculate_total_flight_duration(request.flight_segments)
    
    # 2. 비행 정보 요약
    flight_info = []
    for i, segment in enumerate(request.flight_segments, 1):
        flight_info.append(
            f"구간 {i}: {segment.departure_airport} → {segment.arrival_airport}, "
            f"출발: {segment.departure_time.isoformat()}, "
            f"도착: {segment.arrival_time.isoformat()}"
        )
    
    # 3. 사용자 수면 패턴 정보
    sleep_info = ""
    if request.user_sleep_pattern_start and request.user_sleep_pattern_end:
        sleep_info = f"사용자의 평소 수면 패턴: {request.user_sleep_pattern_start} ~ {request.user_sleep_pattern_end}"
    
    # 4. LLM 프롬프트 구성
    trip_duration = request.trip_duration_days or 7
    prompt = f"""당신은 시차적응(제트랙) 관리 전문가입니다. 다음 정보를 바탕으로 최적의 시차적응 계획을 수립해주세요.

**비행 정보:**
{chr(10).join(flight_info)}

**시간대 정보:**
- 출발지 시간대: {origin_tz}
- 도착지 시간대: {dest_tz}
- 시차: {time_diff}시간
- 총 비행 시간: {total_duration:.1f}시간

**사용자 정보:**
{sleep_info if sleep_info else "사용자 수면 패턴 정보 없음"}
- 여행 기간: {trip_duration}일

**요청사항:**
다음 형식으로 상세한 시차적응 계획을 작성해주세요:

1. **일별 일정** (여행 시작일부터 {trip_duration}일간):
   - 각 날짜별로 다음 정보를 제공:
     * 날짜 (YYYY-MM-DD 형식)
     * 일수 (여행 시작일 기준, 0부터 시작)
     * 현재 위치의 시간대
     * 권장 수면 시간대 (로컬 시간 기준)
     * 권장 식사 시간 (하루 3회, 로컬 시간 기준)
     * 권장 활동 (예: 햇빛 쬐기, 가벼운 운동, 수면 등)
     * 특별 주의사항

2. **일반적인 권장사항** (5-7개 항목):
   - 시차적응을 위한 일반적인 팁

3. **출발 전 팁** (3-5개 항목):
   - 비행 전 준비사항

4. **도착 후 팁** (3-5개 항목):
   - 도착 직후 해야 할 일

5. **알고리즘 설명**:
   - 이 계획이 어떤 원칙과 알고리즘에 기반하여 작성되었는지 설명

**중요한 고려사항:**
- 출발 시간, 도착 시간, 경유지 정보를 모두 고려
- 도착지의 시간대에 맞춰 점진적으로 수면 패턴 조정
- 사용자의 기존 수면 패턴을 최대한 존중하면서 조정
- 경유지가 있다면 각 경유지에서의 시간도 고려
- 비행 중 수면 전략 포함
- 도착 후 첫 3일은 특히 중요하므로 상세히 작성

응답은 JSON 형식이 아닌 자연어로 작성하되, 구조화된 형식을 유지해주세요."""

    system_instruction = (
        "You are a jet lag and circadian rhythm management expert. "
        "Create detailed, personalized jet lag adaptation plans based on flight schedules, "
        "time zones, and user sleep patterns. Consider departure times, arrival times, "
        "layovers, and destination time zones to minimize fatigue and optimize recovery."
    )
    
    # 5. LLM 호출
    llm_request = LLMChatRequest(
        prompt=prompt,
        system_instruction=system_instruction
    )
    
    llm_response = await llm_service.generate_chat_completion(llm_request)
    
    # 6. LLM 응답을 구조화된 데이터로 변환
    # LLM이 자연어로 응답하므로, 응답을 파싱하여 구조화된 데이터 추출
    # 실제 프로덕션에서는 LLM에게 JSON 형식으로 응답하도록 요청하거나,
    # 더 정교한 파싱 로직이 필요합니다.
    
    # 기본 일정 생성 (LLM 응답을 기반으로 개선 가능)
    daily_schedules = _parse_daily_schedules_from_llm(
        llm_response, 
        request.flight_segments[-1].arrival_time.date(),
        dest_tz,
        trip_duration
    )
    
    # 권장사항 및 팁 추출
    general_recommendations = _extract_recommendations(llm_response, "일반적인 권장사항")
    pre_flight_tips = _extract_recommendations(llm_response, "출발 전 팁")
    post_arrival_tips = _extract_recommendations(llm_response, "도착 후 팁")
    
    # 기본값 제공 (LLM 응답에서 추출 실패 시)
    if not general_recommendations:
        general_recommendations = [
            "도착지 시간대에 맞춰 즉시 현지 시간으로 생활하세요.",
            "도착 후 첫 3일은 충분한 수면을 취하세요.",
            "자연광을 충분히 쬐며 신체 리듬을 조정하세요.",
        ]
    
    if not pre_flight_tips:
        pre_flight_tips = [
            "출발 전 며칠간 도착지 시간대에 맞춰 수면 패턴을 조정하세요.",
            "비행 전 충분한 수면을 취하세요.",
        ]
    
    if not post_arrival_tips:
        post_arrival_tips = [
            "도착 후 즉시 현지 시간에 맞춰 식사와 활동을 시작하세요.",
            "낮잠은 20-30분 이내로 제한하세요.",
        ]
    
    return JetLagPlanResponse(
        origin_timezone=origin_tz,
        destination_timezone=dest_tz,
        time_difference_hours=time_diff,
        total_flight_duration_hours=total_duration,
        daily_schedules=daily_schedules,
        general_recommendations=general_recommendations,
        pre_flight_tips=pre_flight_tips,
        post_arrival_tips=post_arrival_tips,
        algorithm_explanation=llm_response
    )


def _parse_daily_schedules_from_llm(
    llm_response: str,
    arrival_date,
    timezone: str,
    duration: int
) -> List[DailySchedule]:
    """
    LLM 응답에서 일별 일정을 파싱합니다.
    실제로는 더 정교한 파싱이 필요하지만, 기본 구조를 제공합니다.
    """
    schedules = []
    
    for day in range(duration):
        current_date = arrival_date + timedelta(days=day)
        
        # LLM 응답에서 해당 날짜의 정보 추출 시도
        # 실제로는 더 정교한 파싱 로직 필요
        sleep_window = "22:00 - 06:00"  # 기본값
        meal_times = ["08:00", "13:00", "19:00"]  # 기본값
        activities = ["가벼운 산책", "햇빛 쬐기"]  # 기본값
        notes = "LLM 응답에서 추출된 정보를 기반으로 일정을 조정하세요."
        
        schedules.append(
            DailySchedule(
                date=current_date.isoformat(),
                day_number=day,
                local_timezone=timezone,
                sleep_window=sleep_window,
                meal_times=meal_times,
                activities=activities,
                notes=notes
            )
        )
    
    return schedules


def _extract_recommendations(llm_response: str, section_name: str) -> List[str]:
    """
    LLM 응답에서 특정 섹션의 권장사항을 추출합니다.
    """
    # 간단한 패턴 매칭으로 추출 시도
    pattern = rf"{section_name}[:\s]*\n((?:[-•]\s*.+\n?)+)"
    match = re.search(pattern, llm_response, re.IGNORECASE | re.MULTILINE)
    
    if match:
        items = []
        for line in match.group(1).split('\n'):
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('•')):
                # "- " 또는 "• " 제거
                item = re.sub(r'^[-•]\s*', '', line).strip()
                if item:
                    items.append(item)
        return items if items else []
    
    return []

