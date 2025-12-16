"""
대한항공 BIMO 요약 강제 갱신 및 확인 스크립트
"""
import asyncio
from app.core.firebase import FirebaseService
from app.feature.llm.gemini_client import get_gemini_client
from app.feature.reviews.reviews_service import ReviewsService


async def main():
    print("=" * 80)
    print("대한항공 BIMO 요약 강제 갱신")
    print("=" * 80)
    
    # Firebase 및 서비스 초기화
    firebase = FirebaseService()
    firebase.initialize()
    
    gemini_client = get_gemini_client()
    reviews_service = ReviewsService(firebase_service=firebase, gemini_client=gemini_client)
    
    # BIMO 요약 업데이트
    print("\n대한항공(KE) BIMO 요약 생성 중...")
    await reviews_service._update_bimo_summary("KE")
    
    # Firebase에서 직접 확인
    print("\nFirebase에서 저장된 BIMO 요약 확인...")
    db = firebase.db
    airline_doc = db.collection("airlines").document("KE").get()
    
    if airline_doc.exists:
        data = airline_doc.to_dict()
        bimo_summary = data.get("bimoSummary", {})
        
        print(f"\n✓ Good 포인트 ({len(bimo_summary.get('goodPoints', []))}개):")
        for i, point in enumerate(bimo_summary.get("goodPoints", []), 1):
            print(f"  {i}. {point}")
        
        print(f"\n✓ Bad 포인트 ({len(bimo_summary.get('badPoints', []))}개):")
        for i, point in enumerate(bimo_summary.get("badPoints", []), 1):
            print(f"  {i}. {point}")
        
        print(f"\n✓ 리뷰 개수: {bimo_summary.get('reviewCount', 0)}개")
        print(f"✓ 마지막 업데이트: {bimo_summary.get('lastUpdated', 'N/A')}")
    else:
        print("✗ 항공사 정보를 찾을 수 없습니다.")
    
    print("\n" + "=" * 80)
    print("완료!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
