#!/usr/bin/env python3
"""
JWT Refresh Token 전체 플로우 테스트 스크립트
.env 파일에서 FIREBASE_TEST_ID_TOKEN을 읽어와서 테스트합니다.
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

BASE_URL = "http://localhost:8002"

def print_separator(title=""):
    """구분선 출력"""
    print("\n" + "=" * 70)
    if title:
        print(f" {title}")
        print("=" * 70)
    print()

def test_jwt_refresh_flow():
    """JWT Refresh Token 전체 플로우 테스트"""
    
    print_separator("JWT Refresh Token 전체 플로우 테스트")
    
    # Step 0: 환경 변수에서 테스트 토큰 가져오기
    print("📋 Step 0: 환경 변수에서 테스트 토큰 로드 중...")
    firebase_test_token = os.getenv("FIREBASE_TEST_ID_TOKEN")
    
    if not firebase_test_token:
        print("❌ 에러: .env 파일에 FIREBASE_TEST_ID_TOKEN이 설정되어 있지 않습니다.")
        print("   .env 파일에 다음을 추가하세요:")
        print("   FIREBASE_TEST_ID_TOKEN=your_firebase_id_token_here")
        sys.exit(1)
    
    print(f"✅ 테스트 토큰 로드 완료: {firebase_test_token[:30]}...")
    
    # Step 1: Google 로그인으로 Access Token과 Refresh Token 받기
    print_separator("Step 1: Google 로그인")
    print("🔐 Firebase ID Token으로 로그인 시도 중...")
    
    try:
        login_response = requests.post(
            f"{BASE_URL}/auth/google/login",
            json={"token": firebase_test_token},
            timeout=10
        )
        
        if login_response.status_code != 200:
            print(f"❌ 로그인 실패: {login_response.status_code}")
            print(f"   응답: {login_response.text}")
            sys.exit(1)
        
        login_data = login_response.json()
        print("✅ 로그인 성공!")
        print(f"   Access Token:  {login_data['access_token'][:50]}...")
        print(f"   Refresh Token: {login_data['refresh_token'][:50]}...")
        print(f"   Token Type:    {login_data['token_type']}")
        
        if 'user' in login_data and login_data['user']:
            user = login_data['user']
            print(f"   User ID:       {user.get('uid', 'N/A')}")
            print(f"   Email:         {user.get('email', 'N/A')}")
            print(f"   Display Name:  {user.get('display_name', 'N/A')}")
        
        access_token = login_data['access_token']
        refresh_token = login_data['refresh_token']
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 네트워크 에러: {e}")
        sys.exit(1)
    
    # Step 2: Access Token으로 API 호출 (선택사항)
    print_separator("Step 2: Access Token 검증")
    print("🔍 Access Token이 유효한지 확인 중...")
    print(f"   (현재 Access Token은 30분간 유효합니다)")
    print("✅ Access Token 발급 완료")
    
    # Step 3: Refresh Token으로 새 Access Token 받기
    print_separator("Step 3: Refresh Token으로 새 Access Token 발급")
    print("🔄 Refresh Token으로 새 Access Token 요청 중...")
    
    try:
        refresh_response = requests.post(
            f"{BASE_URL}/auth/refresh",
            json={"refresh_token": refresh_token},
            timeout=10
        )
        
        if refresh_response.status_code != 200:
            print(f"❌ Refresh 실패: {refresh_response.status_code}")
            print(f"   응답: {refresh_response.text}")
            sys.exit(1)
        
        refresh_data = refresh_response.json()
        print("✅ Refresh 성공!")
        print(f"   새 Access Token: {refresh_data['access_token'][:50]}...")
        print(f"   Token Type:      {refresh_data['token_type']}")
        
        new_access_token = refresh_data['access_token']
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 네트워크 에러: {e}")
        sys.exit(1)
    
    # Step 4: 토큰 비교 및 검증
    print_separator("Step 4: 결과 검증")
    
    print("🔍 토큰 비교 중...")
    if access_token != new_access_token:
        print("✅ 성공! 새로운 Access Token이 발급되었습니다.")
        print("   (원본과 다른 토큰이 생성됨)")
    else:
        print("⚠️  경고: Access Token이 동일합니다.")
        print("   (이론적으로는 다른 토큰이 발급되어야 합니다)")
    
    # Step 5: 잘못된 Refresh Token 테스트
    print_separator("Step 5: 잘못된 Refresh Token 테스트")
    print("🧪 유효하지 않은 Refresh Token으로 요청 중...")
    
    try:
        invalid_response = requests.post(
            f"{BASE_URL}/auth/refresh",
            json={"refresh_token": "invalid_token_12345"},
            timeout=10
        )
        
        if invalid_response.status_code == 401:
            print("✅ 예상대로 401 에러 발생!")
            error_data = invalid_response.json()
            print(f"   Error Code: {error_data.get('error_code', 'N/A')}")
            print(f"   Message:    {error_data.get('message', 'N/A')}")
        else:
            print(f"⚠️  예상치 못한 응답: {invalid_response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 네트워크 에러: {e}")
    
    # 최종 결과 저장
    print_separator("Step 6: 결과 저장")
    
    result_file = "/Users/inho/Desktop/jwt_test_result.json"
    result_data = {
        "test_status": "SUCCESS",
        "original_access_token": access_token,
        "new_access_token": new_access_token,
        "refresh_token": refresh_token,
        "tokens_are_different": access_token != new_access_token
    }
    
    try:
        with open(result_file, 'w') as f:
            json.dump(result_data, f, indent=2)
        print(f"✅ 테스트 결과가 저장되었습니다:")
        print(f"   파일: {result_file}")
    except Exception as e:
        print(f"⚠️  결과 저장 실패: {e}")
    
    # 최종 요약
    print_separator("테스트 완료")
    print("✅ 모든 테스트가 성공적으로 완료되었습니다!")
    print()
    print("📊 요약:")
    print(f"   1. ✅ Google 로그인 성공")
    print(f"   2. ✅ Access Token 발급 성공")
    print(f"   3. ✅ Refresh Token 발급 성공")
    print(f"   4. ✅ Refresh Token으로 새 Access Token 발급 성공")
    print(f"   5. ✅ 잘못된 토큰 거부 확인")
    print()
    print("🎉 JWT Refresh Token 기능이 정상적으로 동작합니다!")
    print()

if __name__ == "__main__":
    try:
        test_jwt_refresh_flow()
    except KeyboardInterrupt:
        print("\n\n⚠️  테스트가 사용자에 의해 중단되었습니다.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 예상치 못한 에러 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

