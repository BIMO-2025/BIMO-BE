"""
실제 사용자 데이터로 타임라인 생성 테스트

사용자 ID와 flight ID를 입력받아 실제 API를 호출하여 타임라인 생성 테스트
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_user_flight_timeline():
    """실제 사용자의 비행편으로 타임라인 생성 테스트"""
    
    # 테스트할 사용자 정보 입력
    print("=" * 70)
    print("실제 사용자 비행편 타임라인 생성 테스트")
    print("=" * 70)
    
    user_id = input("\n사용자 ID를 입력하세요: ").strip()
    if not user_id:
        print("❌ 사용자 ID가 필요합니다.")
        return
    
    flight_id = input("Flight ID를 입력하세요: ").strip()
    if not flight_id:
        print("❌ Flight ID가 필요합니다.")
        return
    
    # Firebase 인증 토큰 (테스트용)
    token = input("Firebase 인증 토큰을 입력하세요 (선택사항, Enter로 건너뛰기): ").strip()
    
    # API 호출
    print(f"\n🔍 요청 정보:")
    print(f"  - 사용자 ID: {user_id}")
    print(f"  - Flight ID: {flight_id}")
    print(f"  - Endpoint: POST /wellness/users/{user_id}/my-flights/{flight_id}/timeline")
    
    # 비행 목표 선택
    print("\n비행 목표를 선택하세요:")
    print("1. SLEEP_FOCUS (수면 집중)")
    print("2. WORK_FOCUS (업무 집중)")  
    print("3. ENTERTAINMENT (휴식/엔터테인먼트)")
    goal_choice = input("선택 (1/2/3, 기본값: 1): ").strip() or "1"
    
    goal_map = {
        "1": "SLEEP_FOCUS",
        "2": "WORK_FOCUS",
        "3": "ENTERTAINMENT"
    }
    flight_goal = goal_map.get(goal_choice, "SLEEP_FOCUS")
    
    # 좌석 등급 선택
    seat_class = input("좌석 등급 (ECONOMY/BUSINESS/FIRST, 기본값: ECONOMY): ").strip() or "ECONOMY"
    
    # 요청 URL
    url = f"{BASE_URL}/wellness/users/{user_id}/my-flights/{flight_id}/timeline"
    params = {
        "flight_goal": flight_goal,
        "seat_class": seat_class
    }
    
    # 헤더 설정
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    print(f"\n📡 API 호출 중...")
    print(f"  - Goal: {flight_goal}")
    print(f"  - Seat: {seat_class}")
    
    try:
        response = requests.post(url, params=params, headers=headers)
        
        print(f"\n📊 응답:")
        print(f"  - Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ 성공!\n")
            
            # 비행 정보
            flight_info = data.get("flight_info", {})
            print("=" * 70)
            print("📍 비행 정보")
            print("=" * 70)
            print(f"  - 출발: {flight_info.get('origin')} → 도착: {flight_info.get('destination')}")
            print(f"  - 출발 시간: {flight_info.get('departure_time')}")
            print(f"  - 도착 시간: {flight_info.get('arrival_time')}")
            print(f"  - 총 소요 시간: {flight_info.get('total_duration')}")
            print(f"  - 좌석: {flight_info.get('seat_class')}")
            print(f"  - 목표: {flight_info.get('flight_goal')}")
            
            # 추천 메시지
            print(f"\n💬 BIMO 추천:")
            print(f"  {data.get('recommendation_message')}")
            
            # 타임라인 이벤트
            events = data.get("timeline_events", [])
            print(f"\n📅 타임라인 이벤트 ({len(events)}개)")
            print("=" * 70)
            
            for event in events:
                icon = {
                    "TAKEOFF": "🛫",
                    "LANDING": "🛬",
                    "MEAL": "🍽️",
                    "SLEEP": "😴",
                    "WORK": "💼",
                    "ENTERTAINMENT": "🎬",
                    "FREE_TIME": "⏰",
                    "LAYOVER": "🔄",
                    "CONNECTION": "🔀"
                }.get(event.get("type"), "📌")
                
                print(f"\n{event.get('order')}. {icon} {event.get('title')}")
                print(f"   타입: {event.get('type')}")
                print(f"   시간: {event.get('display_time')}")
                print(f"   설명: {event.get('description')[:80]}...")
            
            # 경유 이벤트 확인
            layover_events = [e for e in events if e.get('type') in ['LAYOVER', 'CONNECTION']]
            if layover_events:
                print(f"\n🔄 경유 이벤트: {len(layover_events)}개 감지됨")
                for le in layover_events:
                    print(f"   - {le.get('title')}: {le.get('description')[:50]}...")
            
            # 수면 이벤트 확인
            sleep_events = [e for e in events if e.get('type') == 'SLEEP']
            if sleep_events:
                print(f"\n😴 수면 이벤트: {len(sleep_events)}개")
                for se in sleep_events:
                    print(f"   - {se.get('display_time')}: {se.get('description')[:60]}...")
                print(f"\n💡 사용자 수면 패턴이 반영되었는지 확인하세요!")
            
            print("\n" + "=" * 70)
            
            # JSON 저장 옵션
            save = input("\n결과를 JSON 파일로 저장하시겠습니까? (y/n): ").strip().lower()
            if save == 'y':
                filename = f"timeline_result_{user_id}_{flight_id}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"✅ 저장 완료: {filename}")
            
        elif response.status_code == 401:
            print(f"\n❌ 인증 실패: Firebase 토큰이 필요합니다")
            print(f"  {response.text}")
        elif response.status_code == 403:
            print(f"\n❌ 권한 없음: 다른 사용자의 비행편에 접근할 수 없습니다")
            print(f"  {response.text}")
        elif response.status_code == 404:
            print(f"\n❌ 찾을 수 없음: 비행편이 존재하지 않습니다")
            print(f"  {response.text}")
        else:
            print(f"\n❌ 오류 발생:")
            print(f"  {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")


if __name__ == "__main__":
    test_user_flight_timeline()
