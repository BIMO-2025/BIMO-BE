"""
모든 항공사의 BIMO 요약 생성 및 저장
Firebase airlines 컬렉션에 bimoSummary 필드로 저장됨
"""
import asyncio
from app.core.firebase import FirebaseService
from app.feature.llm.gemini_client import get_gemini_client
from app.feature.reviews.reviews_service import ReviewsService


async def generate_all_bimo_summaries():
    """모든 항공사의 BIMO 요약 생성"""
    print("=" * 80)
    print("모든 항공사 BIMO 요약 생성 시작")
    print("=" * 80)
    
    # Firebase 및 서비스 초기화
    firebase = FirebaseService()
    firebase.initialize()
    db = firebase.db
    
    gemini_client = get_gemini_client()
    reviews_service = ReviewsService(firebase_service=firebase, gemini_client=gemini_client)
    
    # 모든 항공사 조회
    print("\n[1단계] 항공사 목록 조회 중...")
    airlines_collection = db.collection("airlines")
    airline_docs = list(airlines_collection.stream())
    
    print(f"✓ 총 {len(airline_docs)}개 항공사 발견")
    
    # 각 항공사별로 BIMO 요약 생성
    print("\n[2단계] BIMO 요약 생성 및 저장 중...")
    
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for idx, airline_doc in enumerate(airline_docs, 1):
        airline_code = airline_doc.id
        airline_data = airline_doc.to_dict()
        airline_name = airline_data.get("airlineName", airline_code)
        total_reviews = airline_data.get("totalReviews", 0)
        
        print(f"\n[{idx}/{len(airline_docs)}] {airline_name} ({airline_code})")
        print(f"  리뷰 개수: {total_reviews}개")
        
        # 리뷰가 없으면 스킵
        if total_reviews == 0:
            print(f"  ⚠️  리뷰 없음 - 스킵")
            skip_count += 1
            continue
        
        try:
            # BIMO 요약 생성 및 저장
            print(f"  🤖 LLM 요약 생성 중...")
            await reviews_service._update_bimo_summary(airline_code)
            
            success_count += 1
            print(f"  ✅ 완료!")
            
            # LLM API 호출 제한을 위해 약간 대기
            if idx < len(airline_docs):
                await asyncio.sleep(2)  # 2초 대기
                
        except Exception as e:
            error_count += 1
            print(f"  ❌ 오류: {e}")
    
    # 결과 출력
    print("\n" + "=" * 80)
    print("BIMO 요약 생성 완료!")
    print("=" * 80)
    print(f"✅ 성공: {success_count}개")
    print(f"⚠️  스킵 (리뷰 없음): {skip_count}개")
    print(f"❌ 오류: {error_count}개")
    print(f"📊 전체: {len(airline_docs)}개")
    print("=" * 80)
    
    # 저장 위치 안내
    print("\n💾 저장 위치:")
    print("Firebase Firestore > airlines > {airlineCode} > bimoSummary")
    print("\n구조:")
    print("""
{
  "bimoSummary": {
    "goodPoints": ["장점1", "장점2", ...],
    "badPoints": ["단점1", "단점2", ...],
    "reviewCount": 30,
    "lastUpdated": "2025-12-15T..."
  }
}
    """)


if __name__ == "__main__":
    asyncio.run(generate_all_bimo_summaries())
