"""
비행 타임라인 API 테스트 스크립트
"""
import requests
import json
from datetime import datetime, timedelta

API_URL = "http://localhost:8000/wellness/flight-timeline"

def test_timeline(scenario_name: str, request_data: dict):
    """타임라인 API 테스트"""
    print(f"\n{'='*80}")
    print(f"테스트 시나리오: {scenario_name}")
    print(f"{'='*80}")
    
    print("\n📤 요청 데이터:")
    print(json.dumps(request_data, indent=2, ensure_ascii=False))
    
    try:
        response = requests.post(API_URL, json=request_data, timeout=30)
        
        print(f"\n📥 응답 상태: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ 성공! 타임라인 이벤트 개수: {len(result['timeline'])}")
            print("\n📋 타임라인 상세:")
            print("-" * 80)
            
            for event in result['timeline']:
                print(f"\n{event['order']}. {event['title']}")
                print(f"   유형: {event['type']} | 아이콘: {event['icon_type']}")
                print(f"   시간: {event['display_time']}")
                print(f"   설명: {event['description']}")
            
            print("\n" + "="*80)
            
        else:
            print(f"\n❌ 오류 발생:")
            print(response.text)
            
    except requests.exceptions.Timeout:
        print("\n⏱️ 타임아웃 발생 (30초 초과)")
    except Exception as e:
        print(f"\n❌ 예외 발생: {e}")


def main():
    """메인 테스트 실행"""
    print("🧪 비행 타임라인 API 테스트 시작")
    
    # 현재 시간 기준
    now = datetime.now()
    departure = now + timedelta(hours=2)
    
    # 시나리오 1: 장거리 비행 - 수면 목표
    test1 = {
        "departure_time": departure.isoformat(),
        "arrival_time": (departure + timedelta(hours=12)).isoformat(),
        "flight_duration_hours": 12,
        "flight_goal": "rest"
    }
    test_timeline("장거리 비행 - 수면 집중", test1)
    
    # 시나리오 2: 중거리 비행 - 업무 목표
    test2 = {
        "departure_time": departure.isoformat(),
        "arrival_time": (departure + timedelta(hours=6)).isoformat(),
        "flight_duration_hours": 6,
        "flight_goal": "work"
    }
    test_timeline("중거리 비행 - 업무 집중", test2)
    
    # 시나리오 3: 단거리 비행 - 엔터테인먼트
    test3 = {
        "departure_time": departure.isoformat(),
        "arrival_time": (departure + timedelta(hours=3)).isoformat(),
        "flight_duration_hours": 3,
        "flight_goal": "entertainment"
    }
    test_timeline("단거리 비행 - 엔터테인먼트", test3)
    
    # 시나리오 4: 초장거리 비행 - 균형잡힌 일정
    test4 = {
        "departure_time": departure.isoformat(),
        "arrival_time": (departure + timedelta(hours=14)).isoformat(),
        "flight_duration_hours": 14,
        "flight_goal": "balanced"
    }
    test_timeline("초장거리 비행 - 균형잡힌 일정", test4)
    
    print("\n" + "="*80)
    print("✨ 모든 테스트 완료!")
    print("="*80)


if __name__ == "__main__":
    main()
