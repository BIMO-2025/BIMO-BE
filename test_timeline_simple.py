"""
비행 타임라인 API 단일 테스트
"""
import requests
import json
from datetime import datetime, timedelta

API_URL = "http://localhost:8000/wellness/flight-timeline"

# 테스트 데이터
departure = datetime.now() + timedelta(hours=2)
request_data = {
    "departure_time": departure.isoformat(),
    "arrival_time": (departure + timedelta(hours=12)).isoformat(),
    "flight_duration_hours": 12,
    "flight_goal": "rest"
}

print("요청 데이터:")
print(json.dumps(request_data, indent=2, ensure_ascii=False))
print("\n" + "="*80 + "\n")

try:
    response = requests.post(API_URL, json=request_data, timeout=30)
    print(f"응답 상태 코드: {response.status_code}\n")
    
    if response.status_code == 200:
        result = response.json()
        print("응답 데이터:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("오류 응답:")
        print(response.text)
        
except Exception as e:
    print(f"예외 발생: {e}")
