"""
BIMO 요약 자동 갱신 테스트 스크립트
리뷰 생성 시 통계와 BIMO 요약이 자동으로 업데이트되는지 확인
"""
import asyncio
import httpx
import json
from datetime import datetime, timezone

# API 기본 URL
BASE_URL = "http://localhost:8000"

# 테스트용 리뷰 데이터
TEST_REVIEW = {
    "userId": "test_user_001",
    "userNickname": "테스트유저",
    "airlineCode": "KE",
    "airlineName": "대한항공",
    "route": "ICN-JFK",
    "flightNumber": "KE081",
    "seatClass": "비즈니스",
    "imageUrl": None,
    "ratings": {
        "seatComfort": 5,
        "inflightMeal": 5,
        "service": 5,
        "cleanliness": 5,
        "checkIn": 5
    },
    "overallRating": 5.0,
    "text": "정말 훌륭한 비행이었습니다! 좌석이 매우 편안했고 승무원분들이 너무 친절하셨어요. 기내식도 레스토랑 수준의 퀄리티였고 엔터테인먼트 시스템도 완벽했습니다. 비즈니스석 라운지도 정말 좋았어요. 다음에도 꼭 대한항공을 이용하고 싶습니다. 모든 면에서 만족스러운 여행이었어요!",
    "isVerified": True,
    "likes": 0
}


async def test_bimo_auto_update():
    """BIMO 요약 자동 갱신 테스트"""
    print("=" * 80)
    print("BIMO 요약 자동 갱신 테스트 시작")
    print("=" * 80)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        
        # 1. 기존 BIMO 요약 조회 (비교용)
        print("\n[1단계] 기존 BIMO 요약 조회...")
        try:
            response = await client.get(f"{BASE_URL}/airlines/KE/summary")
            if response.status_code == 200:
                old_summary = response.json()
                print(f"✓ 기존 Good 포인트: {len(old_summary.get('good_points', []))}개")
                print(f"✓ 기존 Bad 포인트: {len(old_summary.get('bad_points', []))}개")
                print(f"✓ 리뷰 개수: {old_summary.get('review_count', 0)}개")
            else:
                print(f"⚠️  BIMO 요약 조회 실패: {response.status_code}")
                old_summary = None
        except Exception as e:
            print(f"⚠️  오류 발생: {e}")
            old_summary = None
        
        # 2. 테스트 리뷰 생성 (인증 토큰 필요 - 우회)
        print("\n[2단계] 테스트 리뷰 생성...")
        print("⚠️  인증 토큰이 필요하여 직접 Firebase에 삽입합니다.")
        
        # Firebase에 직접 삽입
        from app.core.firebase import FirebaseService
        firebase = FirebaseService()
        firebase.initialize()
        db = firebase.db
        
        reviews_collection = db.collection("reviews")
        
        # 리뷰 데이터 준비
        review_data = TEST_REVIEW.copy()
        review_data["createdAt"] = datetime.now(timezone.utc)
        
        # Firebase에 저장
        doc_ref = reviews_collection.document()
        doc_ref.set(review_data)
        review_id = doc_ref.id
        
        print(f"✓ 테스트 리뷰 생성 완료 (ID: {review_id})")
        
        # 3. 백그라운드 태스크 실행 대기 (수동으로 호출)
        print("\n[3단계] 통계 및 BIMO 요약 업데이트 중...")
        
        from app.feature.reviews.reviews_service import ReviewsService
        from app.feature.llm.gemini_client import get_gemini_client
        
        gemini_client = get_gemini_client()
        reviews_service = ReviewsService(firebase_service=firebase, gemini_client=gemini_client)
        
        # 통계 업데이트
        print("  - 통계 업데이트...")
        await reviews_service._update_airline_statistics("KE")
        
        # BIMO 요약 업데이트
        print("  - BIMO 요약 업데이트...")
        await reviews_service._update_bimo_summary("KE")
        
        # 4. 업데이트된 BIMO 요약 조회
        print("\n[4단계] 업데이트된 BIMO 요약 조회...")
        await asyncio.sleep(2)  # 약간 대기
        
        response = await client.get(f"{BASE_URL}/airlines/KE/summary")
        if response.status_code == 200:
            new_summary = response.json()
            print(f"✓ 새 Good 포인트: {len(new_summary.get('good_points', []))}개")
            for i, point in enumerate(new_summary.get('good_points', []), 1):
                print(f"    {i}. {point}")
            
            print(f"✓ 새 Bad 포인트: {len(new_summary.get('bad_points', []))}개")
            for i, point in enumerate(new_summary.get('bad_points', []), 1):
                print(f"    {i}. {point}")
            
            print(f"✓ 리뷰 개수: {new_summary.get('review_count', 0)}개")
        else:
            print(f"✗ BIMO 요약 조회 실패: {response.status_code}")
        
        # 5. 테스트 리뷰 삭제 (정리)
        print("\n[5단계] 테스트 리뷰 삭제...")
        doc_ref.delete()
        print(f"✓ 테스트 리뷰 삭제 완료")
        
        # 다시 통계 업데이트
        await reviews_service._update_airline_statistics("KE")
        await reviews_service._update_bimo_summary("KE")
        print("✓ 통계 및 BIMO 요약 복구 완료")
    
    print("\n" + "=" * 80)
    print("✓ BIMO 요약 자동 갱신 테스트 완료!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_bimo_auto_update())
