"""
자동 타임라인 생성 테스트 - LLM 응답 전체 기록

가짜 사용자 데이터로 타임라인 서비스를 직접 호출하고 
LLM 응답을 파일에 기록합니다.
"""

import asyncio
import json
from datetime import datetime, timezone, timedelta
from app.feature.wellness import flight_timeline_service
from app.feature.wellness.flight_timeline_schemas import (
    FlightTimelineRequest,
    FlightSegmentInfo
)

async def test_timeline_with_full_logging():
    """가짜 데이터로 타임라인 생성 테스트 및 로깅"""
    
    print("=" * 80)
    print("자동 타임라인 생성 테스트 - LLM 응답 전체 기록")
    print("=" * 80)
    
    # 테스트 케이스 1: 경유 1회, 수면 패턴 포함
    print("\n[테스트 1] 경유 1회 + 수면 패턴")
    print("-" * 80)
    
    test1_request = FlightTimelineRequest(
        origin="ICN",
        destination="JFK",
        departure_time=datetime(2025, 12, 25, 22, 0, tzinfo=timezone.utc),  # 한국 시간 오후 10시
        arrival_time=datetime(2025, 12, 26, 14, 30, tzinfo=timezone.utc),   # 뉴욕 시간 오전 9:30
        seat_class="ECONOMY",
        flight_goal="SLEEP_FOCUS",
        segments=[
            FlightSegmentInfo(
                origin="ICN",
                destination="NRT",
                departure_time=datetime(2025, 12, 25, 22, 0, tzinfo=timezone.utc),
                arrival_time=datetime(2025, 12, 26, 1, 30, tzinfo=timezone.utc),
                duration="3h 30m"
            ),
            FlightSegmentInfo(
                origin="NRT",
                destination="JFK",
                departure_time=datetime(2025, 12, 26, 3, 30, tzinfo=timezone.utc),
                arrival_time=datetime(2025, 12, 26, 14, 30, tzinfo=timezone.utc),
                duration="11h 0m"
            )
        ],
        user_sleep_pattern={
            "sleep_start": "23:30",
            "sleep_end": "07:00"
        }
    )
    
    print(f"출발: {test1_request.origin} → 도착: {test1_request.destination}")
    print(f"경유: NRT (2시간 대기)")
    print(f"수면 패턴: {test1_request.user_sleep_pattern['sleep_start']} ~ {test1_request.user_sleep_pattern['sleep_end']}")
    print("\n🔄 LLM 호출 중...")
    
    try:
        result1 = await flight_timeline_service.generate_flight_timeline(test1_request)
        
        # 결과를 JSON 파일로 저장
        result1_dict = {
            "test_case": "경유 1회 + 수면 패턴",
            "request": {
                "origin": test1_request.origin,
                "destination": test1_request.destination,
                "departure_time": test1_request.departure_time.isoformat(),
                "arrival_time": test1_request.arrival_time.isoformat(),
                "seat_class": test1_request.seat_class,
                "flight_goal": test1_request.flight_goal,
                "segments": [
                    {
                        "origin": seg.origin,
                        "destination": seg.destination,
                        "departure_time": seg.departure_time.isoformat(),
                        "arrival_time": seg.arrival_time.isoformat(),
                        "duration": seg.duration
                    } for seg in test1_request.segments
                ],
                "user_sleep_pattern": test1_request.user_sleep_pattern
            },
            "response": result1.model_dump()
        }
        
        filename1 = f"timeline_test_1_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename1, 'w', encoding='utf-8') as f:
            json.dump(result1_dict, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 테스트 1 완료 - 저장: {filename1}")
        print(f"   이벤트 수: {len(result1.timeline_events)}")
        print(f"   이벤트 타입: {[e.type for e in result1.timeline_events]}")
        
        # 경유 이벤트 확인
        layover_events = [e for e in result1.timeline_events if e.type in ['LAYOVER', 'CONNECTION']]
        if layover_events:
            print(f"   ✓ 경유 이벤트 {len(layover_events)}개 감지")
        
        # 수면 이벤트 확인
        sleep_events = [e for e in result1.timeline_events if e.type == 'SLEEP']
        if sleep_events:
            print(f"   ✓ 수면 이벤트 {len(sleep_events)}개")
            for se in sleep_events:
                print(f"      - {se.display_time}")
        
    except Exception as e:
        print(f"❌ 테스트 1 실패: {e}")
        import traceback
        traceback.print_exc()
    
    # 테스트 케이스 2: 경유 2회, 수면 패턴 없음
    print("\n[테스트 2] 경유 2회 + 수면 패턴 없음")
    print("-" * 80)
    
    test2_request = FlightTimelineRequest(
        origin="ICN",
        destination="JFK",
        departure_time=datetime(2025, 12, 25, 10, 0, tzinfo=timezone.utc),
        arrival_time=datetime(2025, 12, 26, 17, 0, tzinfo=timezone.utc),
        seat_class="BUSINESS",
        flight_goal="WORK_FOCUS",
        segments=[
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
        ],
        user_sleep_pattern=None
    )
    
    print(f"출발: {test2_request.origin} → 도착: {test2_request.destination}")
    print(f"경유: DXB (7시간 대기), LHR (2시간 대기)")
    print(f"수면 패턴: 없음 (일반적인 패턴 가정)")
    print("\n🔄 LLM 호출 중...")
    
    try:
        result2 = await flight_timeline_service.generate_flight_timeline(test2_request)
        
        result2_dict = {
            "test_case": "경유 2회 + 수면 패턴 없음",
            "request": {
                "origin": test2_request.origin,
                "destination": test2_request.destination,
                "departure_time": test2_request.departure_time.isoformat(),
                "arrival_time": test2_request.arrival_time.isoformat(),
                "seat_class": test2_request.seat_class,
                "flight_goal": test2_request.flight_goal,
                "segments": [
                    {
                        "origin": seg.origin,
                        "destination": seg.destination,
                        "departure_time": seg.departure_time.isoformat(),
                        "arrival_time": seg.arrival_time.isoformat(),
                        "duration": seg.duration
                    } for seg in test2_request.segments
                ],
                "user_sleep_pattern": test2_request.user_sleep_pattern
            },
            "response": result2.model_dump()
        }
        
        filename2 = f"timeline_test_2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename2, 'w', encoding='utf-8') as f:
            json.dump(result2_dict, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 테스트 2 완료 - 저장: {filename2}")
        print(f"   이벤트 수: {len(result2.timeline_events)}")
        print(f"   이벤트 타입: {[e.type for e in result2.timeline_events]}")
        
        layover_events = [e for e in result2.timeline_events if e.type in ['LAYOVER', 'CONNECTION']]
        if layover_events:
            print(f"   ✓ 경유 이벤트 {len(layover_events)}개 감지")
            for le in layover_events:
                print(f"      - {le.title}")
        
    except Exception as e:
        print(f"❌ 테스트 2 실패: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("테스트 완료! JSON 파일에 LLM 응답 전체가 저장되었습니다.")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_timeline_with_full_logging())
