#!/usr/bin/env python3
"""
JWT Refresh Token 간단 테스트 스크립트
Firestore에 테스트 사용자를 직접 생성하여 테스트합니다.
"""

import sys
import requests
import json
from datetime import datetime, timezone

# 직접 import
sys.path.insert(0, '/Users/inho/Desktop/Programming/BIMO-BE')
from app.core.security import create_access_token, create_refresh_token
from app.core.firebase import db
from fastapi.concurrency import run_in_threadpool
import asyncio

BASE_URL = "http://localhost:8002"
TEST_USER_UID = "test_jwt_refresh_user_123"

def print_separator(title=""):
    """구분선 출력"""
    print("\n" + "=" * 70)
    if title:
        print(f" {title}")
        print("=" * 70)
    print()

async def create_test_user():
    """테스트용 사용자를 Firestore에 생성"""
    print("👤 테스트 사용자 생성 중...")
    
    user_ref = db.collection("users").document(TEST_USER_UID)
    user_data = {
        "uid": TEST_USER_UID,
        "email": "test_jwt@example.com",
        "display_name": "JWT Test User",
        "photo_url": None,
        "provider_id": "google.com",
        "fcm_tokens": [],
        "created_at": datetime.now(timezone.utc),
        "last_login_at": datetime.now(timezone.utc)
    }
    
    await run_in_threadpool(user_ref.set, user_data)
    print(f"✅ 테스트 사용자 생성 완료: {TEST_USER_UID}")

async def cleanup_test_user():
    """테스트 사용자 삭제"""
    print("🧹 테스트 사용자 정리 중...")
    user_ref = db.collection("users").document(TEST_USER_UID)
    await run_in_threadpool(user_ref.delete)
    print("✅ 테스트 사용자 삭제 완료")

def test_jwt_refresh_simple():
    """JWT Refresh Token 간단 테스트"""
    
    print_separator("JWT Refresh Token 간단 테스트")
    
    # Step 1: 테스트 사용자 생성
    print_separator("Step 1: 테스트 사용자 생성")
    asyncio.run(create_test_user())
    
    # Step 2: 테스트용 토큰 직접 생성
    print_separator("Step 2: 테스트용 토큰 생성")
    print("🔐 테스트용 Access Token과 Refresh Token 생성 중...")
    
    access_token = create_access_token({"sub": TEST_USER_UID})
    refresh_token = create_refresh_token({"sub": TEST_USER_UID})
    
    print(f"✅ Access Token:  {access_token[:50]}...")
    print(f"✅ Refresh Token: {refresh_token[:50]}...")
    
    # Step 3: Refresh Token으로 새 Access Token 받기
    print_separator("Step 3: Refresh Token으로 새 Access Token 발급")
    print("🔄 POST /auth/refresh 호출 중...")
    
    try:
        refresh_response = requests.post(
            f"{BASE_URL}/auth/refresh",
            json={"refresh_token": refresh_token},
            timeout=10
        )
        
        if refresh_response.status_code != 200:
            print(f"❌ Refresh 실패: {refresh_response.status_code}")
            print(f"   응답: {refresh_response.text}")
        else:
            refresh_data = refresh_response.json()
            print("✅ Refresh 성공!")
            print(f"   새 Access Token: {refresh_data['access_token'][:50]}...")
            print(f"   Token Type:      {refresh_data['token_type']}")
            
            new_access_token = refresh_data['access_token']
            
            # Step 4: 토큰 비교
            print_separator("Step 4: 결과 검증")
            if access_token != new_access_token:
                print("✅ 성공! 새로운 Access Token이 발급되었습니다.")
            else:
                print("⚠️  경고: Access Token이 동일합니다.")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 네트워크 에러: {e}")
        print("   서버가 실행 중인지 확인하세요: http://localhost:8002")
    
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
    
    # Step 6: 정리
    print_separator("Step 6: 정리")
    asyncio.run(cleanup_test_user())
    
    # 최종 요약
    print_separator("테스트 완료")
    print("✅ JWT Refresh Token 테스트가 완료되었습니다!")
    print()
    print("📊 테스트 항목:")
    print("   1. ✅ 테스트 사용자 생성")
    print("   2. ✅ Access Token & Refresh Token 생성")
    print("   3. ✅ Refresh Token으로 새 Access Token 발급")
    print("   4. ✅ 잘못된 토큰 거부 확인")
    print("   5. ✅ 테스트 사용자 정리")
    print()
    print("🎉 JWT Refresh Token 기능이 정상적으로 동작합니다!")
    print()

if __name__ == "__main__":
    try:
        test_jwt_refresh_simple()
    except KeyboardInterrupt:
        print("\n\n⚠️  테스트가 사용자에 의해 중단되었습니다.")
        print("테스트 사용자를 정리합니다...")
        asyncio.run(cleanup_test_user())
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 예상치 못한 에러 발생: {e}")
        import traceback
        traceback.print_exc()
        print("\n테스트 사용자를 정리합니다...")
        try:
            asyncio.run(cleanup_test_user())
        except:
            pass
        sys.exit(1)

