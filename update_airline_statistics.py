"""
항공사별 통계 데이터 업데이트 스크립트
reviews 컬렉션 데이터를 기반으로 airlines 컬렉션의 통계를 업데이트합니다.
"""
import os
import sys
from collections import defaultdict
from dotenv import load_dotenv

# Windows 콘솔 인코딩 설정
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from app.core.firebase import FirebaseService


def calculate_airline_statistics(reviews):
    """
    리뷰 목록을 기반으로 항공사 통계 계산
    
    Args:
        reviews: 리뷰 문서 리스트
        
    Returns:
        통계 딕셔너리
    """
    if not reviews:
        return {
            "totalReviews": 0,
            "totalRatingSums": {},
            "averageRatings": {},
            "ratingBreakdown": {},
            "overallRating": 0.0
        }
    
    # 카테고리별 평점 합계
    rating_sums = {
        "seatComfort": 0,
        "inflightMeal": 0,
        "service": 0,
        "cleanliness": 0,
        "checkIn": 0
    }
    
    # 전체 평점 합계
    overall_rating_sum = 0.0
    
    # 평점 분포 (1점~5점)
    rating_breakdown = {
        "1": 0,
        "2": 0,
        "3": 0,
        "4": 0,
        "5": 0
    }
    
    # 리뷰 데이터 집계
    for review in reviews:
        review_data = review.to_dict()
        
        # 카테고리별 평점 누적
        ratings = review_data.get("ratings", {})
        for category in rating_sums.keys():
            rating_sums[category] += ratings.get(category, 0)
        
        # 전체 평점 누적
        overall = review_data.get("overallRating", 0.0)
        overall_rating_sum += overall
        
        # 평점 분포 계산 (반올림)
        rating_key = str(round(overall))
        if rating_key in rating_breakdown:
            rating_breakdown[rating_key] += 1
    
    # 평균 계산
    total_reviews = len(reviews)
    average_ratings = {
        category: round(sum_value / total_reviews, 2)
        for category, sum_value in rating_sums.items()
    }
    
    overall_rating = round(overall_rating_sum / total_reviews, 2)
    
    return {
        "totalReviews": total_reviews,
        "totalRatingSums": rating_sums,
        "averageRatings": average_ratings,
        "ratingBreakdown": rating_breakdown,
        "overallRating": overall_rating
    }


def main():
    """메인 실행 함수"""
    print("=" * 80)
    print("항공사 통계 데이터 업데이트")
    print("=" * 80)
    
    # Firebase 서비스 초기화
    firebase_service = FirebaseService()
    firebase_service.initialize()
    db = firebase_service.db
    
    airlines_collection = db.collection("airlines")
    reviews_collection = db.collection("reviews")
    
    # 1. 항공사 목록 조회
    print("\n[1단계] 항공사 목록 조회 중...")
    airlines_docs = list(airlines_collection.stream())
    print(f"✓ 총 {len(airlines_docs)}개 항공사 발견")
    
    # 2. 각 항공사별로 리뷰를 조회하고 통계 계산
    print("\n[2단계] 항공사별 통계 계산 및 업데이트 중...")
    
    updated_count = 0
    
    for idx, airline_doc in enumerate(airlines_docs, 1):
        airline_code = airline_doc.id
        airline_data = airline_doc.to_dict()
        airline_name = airline_data.get("airlineName", airline_code)
        
        print(f"\n진행: [{idx}/{len(airlines_docs)}] {airline_name} ({airline_code})")
        
        # 해당 항공사의 모든 리뷰 조회
        reviews_query = reviews_collection.where("airlineCode", "==", airline_code)
        reviews = list(reviews_query.stream())
        
        print(f"  - 리뷰 개수: {len(reviews)}개")
        
        # 통계 계산
        statistics = calculate_airline_statistics(reviews)
        
        print(f"  - 전체 평점: {statistics['overallRating']}")
        print(f"  - 평균 평점: {statistics['averageRatings']}")
        
        # airlines 컬렉션 업데이트
        airline_ref = airlines_collection.document(airline_code)
        airline_ref.update(statistics)
        
        updated_count += 1
        print(f"  ✓ 업데이트 완료")
    
    # 3. 결과 출력
    print("\n" + "=" * 80)
    print("통계 업데이트 완료!")
    print("=" * 80)
    print(f"✓ 업데이트된 항공사: {updated_count}개")
    print("=" * 80)
    
    # 4. 검증: 첫 번째 항공사 확인
    if airlines_docs:
        first_airline_code = airlines_docs[0].id
        first_airline_name = airlines_docs[0].to_dict().get("airlineName", first_airline_code)
        
        # 업데이트된 데이터 조회
        updated_doc = airlines_collection.document(first_airline_code).get()
        updated_data = updated_doc.to_dict()
        
        print(f"\n[검증] {first_airline_name} ({first_airline_code}) 업데이트 확인:")
        print(f"  - totalReviews: {updated_data.get('totalReviews')}개")
        print(f"  - overallRating: {updated_data.get('overallRating')}")
        print(f"  - averageRatings: {updated_data.get('averageRatings')}")


if __name__ == "__main__":
    main()
