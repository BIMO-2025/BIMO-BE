"""
리뷰 데이터 검증 스크립트
삽입된 리뷰 데이터가 올바른지 확인합니다.
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Windows 콘솔 인코딩 설정
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from app.core.firebase import FirebaseService


def main():
    """메인 실행 함수"""
    print("=" * 80)
    print("리뷰 데이터 검증")
    print("=" * 80)
    
    # Firebase 서비스 초기화
    firebase_service = FirebaseService()
    firebase_service.initialize()
    db = firebase_service.db
    
    airlines_collection = db.collection("airlines")
    reviews_collection = db.collection("reviews")
    
    # 1. 전체 리뷰 개수 확인
    print("\n[1단계] 전체 리뷰 개수 확인")
    all_reviews = list(reviews_collection.stream())
    total_reviews = len(all_reviews)
    print(f"✓ 전체 리뷰 개수: {total_reviews}개")
    
    # 2. 항공사별 리뷰 개수 확인
    print("\n[2단계] 항공사별 리뷰 개수 확인")
    airlines_docs = list(airlines_collection.stream())
    print(f"✓ 전체 항공사 수: {len(airlines_docs)}개\n")
    
    airline_review_counts = {}
    
    for airline_doc in airlines_docs:
        airline_code = airline_doc.id
        airline_name = airline_doc.to_dict().get("airlineName", airline_code)
        
        # 해당 항공사의 리뷰 개수 조회
        reviews_query = reviews_collection.where("airlineCode", "==", airline_code)
        reviews_count = len(list(reviews_query.stream()))
        
        airline_review_counts[airline_code] = {
            "name": airline_name,
            "count": reviews_count
        }
    
    # 리뷰 개수별로 그룹화
    counts_distribution = {}
    for code, data in airline_review_counts.items():
        count = data["count"]
        if count not in counts_distribution:
            counts_distribution[count] = []
        counts_distribution[count].append((code, data["name"]))
    
    print("📊 항공사별 리뷰 개수 분포:")
    for count in sorted(counts_distribution.keys(), reverse=True):
        airlines = counts_distribution[count]
        print(f"  {count}개 리뷰: {len(airlines)}개 항공사")
        if count != 10:  # 10개가 아닌 경우 상세 정보 출력
            for code, name in airlines[:5]:  # 최대 5개만 출력
                print(f"    - {name} ({code})")
            if len(airlines) > 5:
                print(f"    ... 외 {len(airlines) - 5}개")
    
    # 3. 샘플 리뷰 데이터 확인
    print("\n[3단계] 샘플 리뷰 데이터 확인")
    sample_reviews = all_reviews[:3]  # 처음 3개만
    
    for idx, review_doc in enumerate(sample_reviews, 1):
        review_data = review_doc.to_dict()
        print(f"\n샘플 리뷰 #{idx} (ID: {review_doc.id}):")
        print(f"  항공사: {review_data.get('airlineName')} ({review_data.get('airlineCode')})")
        print(f"  작성자: {review_data.get('userNickname')}")
        print(f"  노선: {review_data.get('route')}")
        print(f"  좌석 등급: {review_data.get('seatClass')}")
        print(f"  전체 평점: {review_data.get('overallRating')}")
        print(f"  세부 평점: {review_data.get('ratings')}")
        print(f"  좋아요: {review_data.get('likes')}개")
        print(f"  인증 여부: {'✓' if review_data.get('isVerified') else '✗'}")
        print(f"  작성일: {review_data.get('createdAt')}")
        print(f"  리뷰 내용: {review_data.get('text')[:50]}...")
    
    # 4. 스키마 검증
    print("\n[4단계] 스키마 검증")
    required_fields = [
        "userId", "userNickname", "airlineCode", "airlineName", "route",
        "ratings", "overallRating", "text", "isVerified", "likes", "createdAt"
    ]
    
    schema_errors = []
    for review_doc in all_reviews[:100]:  # 처음 100개만 검증
        review_data = review_doc.to_dict()
        for field in required_fields:
            if field not in review_data:
                schema_errors.append(f"리뷰 {review_doc.id}에 필수 필드 '{field}'가 없습니다.")
    
    if schema_errors:
        print(f"⚠️  스키마 오류 발견: {len(schema_errors)}개")
        for error in schema_errors[:10]:  # 최대 10개만 출력
            print(f"  - {error}")
    else:
        print("✓ 스키마 검증 완료: 모든 필수 필드가 존재합니다.")
    
    # 5. 최종 요약
    print("\n" + "=" * 80)
    print("검증 결과 요약")
    print("=" * 80)
    print(f"✓ 전체 리뷰 개수: {total_reviews}개")
    print(f"✓ 전체 항공사 수: {len(airlines_docs)}개")
    print(f"✓ 예상 리뷰 개수: {len(airlines_docs) * 10}개")
    
    if total_reviews == len(airlines_docs) * 10:
        print(f"✅ 성공: 모든 항공사에 리뷰 10개씩 정확히 삽입되었습니다!")
    else:
        print(f"⚠️  주의: 예상 개수와 실제 개수가 다릅니다.")
        print(f"   차이: {total_reviews - len(airlines_docs) * 10}개")
    
    # 10개가 아닌 항공사 목록
    non_ten_airlines = [
        (code, data["name"], data["count"]) 
        for code, data in airline_review_counts.items() 
        if data["count"] != 10
    ]
    
    if non_ten_airlines:
        print(f"\n⚠️  리뷰가 10개가 아닌 항공사: {len(non_ten_airlines)}개")
        for code, name, count in non_ten_airlines[:10]:
            print(f"   - {name} ({code}): {count}개")
    
    print("=" * 80)


if __name__ == "__main__":
    main()
