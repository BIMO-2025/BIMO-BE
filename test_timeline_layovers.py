# 타임라인 생성 테스트 스크립트
# 경유 0개(직항), 1개, 2개 케이스 테스트

import requests
import json
from datetime import datetime, timezone, timedelta

BASE_URL = "http://localhost:8000"

def test_direct_flight():
    """경유 0개 - 직항 항공편"""
    print("\n=== 테스트 1: 직항 항공편 (경유 0개) ===")
    print("ICN → JFK (12h 30m)")
    
    payload = {
        "origin": "ICN",
        "destination": "JFK",
        "departure_time": "2025-12-25T10:00:00Z",
        "arrival_time": "2025-12-25T22:30:00Z",
        "seat_class": "ECONOMY",
        "flight_goal": "SLEEP_FOCUS",
        "total_duration": "12h 30m"
    }
    
    response = requests.post(f"{BASE_URL}/wellness/flight-timeline", json=payload)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 성공!")
        print(f"  - 추천 메시지: {data.get('recommendation_message')}")
        print(f"  - 이벤트 개수: {len(data.get('timeline_events', []))}")
        print(f"  - 이벤트 타입: {[e['type'] for e in data.get('timeline_events', [])]}")
    else:
        print(f"❌ 실패: {response.text}")
    
    return response.json() if response.status_code == 200 else None


def test_one_layover():
    """경유 1개 - 1회 경유"""
    print("\n=== 테스트 2: 1회 경유 (경유 1개) ===")
    print("ICN → NRT (3h 30m) → 경유 2h → NRT → JFK (11h)")
    print("총 소요: 16h 30m, 순수 비행: 14h 30m")
    
    payload = {
        "origin": "ICN",
        "destination": "JFK",
        "departure_time": "2025-12-25T10:00:00Z",
        "arrival_time": "2025-12-26T02:30:00Z",
        "seat_class": "ECONOMY",
        "flight_goal": "SLEEP_FOCUS",
        "segments": [
            {
                "origin": "ICN",
                "destination": "NRT",
                "departure_time": "2025-12-25T10:00:00Z",
                "arrival_time": "2025-12-25T13:30:00Z",
                "duration": "3h 30m"
            },
            {
                "origin": "NRT",
                "destination": "JFK",
                "departure_time": "2025-12-25T15:30:00Z",
                "arrival_time": "2025-12-26T02:30:00Z",
                "duration": "11h 0m"
            }
        ]
    }
    
    response = requests.post(f"{BASE_URL}/wellness/flight-timeline", json=payload)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 성공!")
        print(f"  - 추천 메시지: {data.get('recommendation_message')}")
        print(f"  - 이벤트 개수: {len(data.get('timeline_events', []))}")
        print(f"  - 이벤트 타입: {[e['type'] for e in data.get('timeline_events', [])]}")
        
        # LAYOVER 이벤트 확인
        layover_events = [e for e in data.get('timeline_events', []) if e['type'] in ['LAYOVER', 'CONNECTION']]
        if layover_events:
            print(f"  - 경유 이벤트: {len(layover_events)}개")
            for le in layover_events:
                print(f"    * {le['title']}: {le['description'][:50]}...")
    else:
        print(f"❌ 실패: {response.text}")
    
    return response.json() if response.status_code == 200 else None


def test_two_layovers():
    """경유 2개 - 2회 경유"""
    print("\n=== 테스트 3: 2회 경유 (경유 2개) ===")
    print("ICN → DXB (8h) → 경유 7h → DXB → LHR (7h) → 경유 2h → LHR → JFK (7h)")
    print("총 소요: 31h, 순수 비행: 22h")
    
    payload = {
        "origin": "ICN",
        "destination": "JFK",
        "departure_time": "2025-12-25T10:00:00Z",
        "arrival_time": "2025-12-26T17:00:00Z",
        "seat_class": "BUSINESS",
        "flight_goal": "WORK_FOCUS",
        "segments": [
            {
                "origin": "ICN",
                "destination": "DXB",
                "departure_time": "2025-12-25T10:00:00Z",
                "arrival_time": "2025-12-25T18:00:00Z",
                "duration": "8h 0m"
            },
            {
                "origin": "DXB",
                "destination": "LHR",
                "departure_time": "2025-12-26T01:00:00Z",
                "arrival_time": "2025-12-26T08:00:00Z",
                "duration": "7h 0m"
            },
            {
                "origin": "LHR",
                "destination": "JFK",
                "departure_time": "2025-12-26T10:00:00Z",
                "arrival_time": "2025-12-26T17:00:00Z",
                "duration": "7h 0m"
            }
        ]
    }
    
    response = requests.post(f"{BASE_URL}/wellness/flight-timeline", json=payload)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 성공!")
        print(f"  - 추천 메시지: {data.get('recommendation_message')}")
        print(f"  - 이벤트 개수: {len(data.get('timeline_events', []))}")
        print(f"  - 이벤트 타입: {[e['type'] for e in data.get('timeline_events', [])]}")
        
        # LAYOVER 이벤트 확인
        layover_events = [e for e in data.get('timeline_events', []) if e['type'] in ['LAYOVER', 'CONNECTION']]
        if layover_events:
            print(f"  - 경유 이벤트: {len(layover_events)}개")
            for le in layover_events:
                print(f"    * {le['title']}: {le['description'][:50]}...")
    else:
        print(f"❌ 실패: {response.text}")
    
    return response.json() if response.status_code == 200 else None


if __name__ == "__main__":
    print("=" * 70)
    print("타임라인 생성 테스트 - 경유 0/1/2개")
    print("=" * 70)
    
    try:
        # 테스트 1: 직항
        result1 = test_direct_flight()
        
        # 테스트 2: 1회 경유
        result2 = test_one_layover()
        
        # 테스트 3: 2회 경유
        result3 = test_two_layovers()
        
        print("\n" + "=" * 70)
        print("테스트 완료!")
        print("=" * 70)
        
        # 결과 요약
        results = [result1, result2, result3]
        success_count = sum(1 for r in results if r is not None)
        print(f"\n성공: {success_count}/3")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
