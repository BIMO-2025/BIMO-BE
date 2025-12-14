"""
항공사 API 테스트 스크립트
업데이트된 통계 데이터가 제대로 반환되는지 확인합니다.
"""
import os
import sys
from dotenv import load_dotenv

# Windows 콘솔 인코딩 설정
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from app.core.firebase import FirebaseService
from app.feature.airlines.airline_service import AirlineService


async def main():
    """메인 실행 함수"""
    print("=" * 80)
    print("항공사 API 테스트")
    print("=" * 80)
    
    # Firebase 서비스 초기화
    firebase_service = FirebaseService()
    firebase_service.initialize()
    
    # AirlineService 초기화
    airline_service = AirlineService(firebase_service=firebase_service)
    
    # 테스트할 항공사 코드 (Korean Air)
    test_airline_code = "KE"
    
    print(f"\n[테스트] 항공사 코드: {test_airline_code}")
    print("-" * 80)
    
    # 1. get_airline_statistics() 테스트
    print("\n[1] get_airline_statistics() 호출:")
    stats = await airline_service.get_airline_statistics(test_airline_code)
    
    if stats:
        print(f"  ✓ 항공사 이름: {stats.airlineName}")
        print(f"  ✓ 총 리뷰 수: {stats.totalReviews}개")
        print(f"  ✓ 전체 평점: {stats.overallRating}")
        print(f"  ✓ 카테고리별 평균 평점:")
        for category, rating in stats.averageRatings.items():
            print(f"      - {category}: {rating}")
        print(f"  ✓ 평점 분포: {stats.ratingBreakdown}")
    else:
        print("  ✗ 항공사를 찾을 수 없습니다.")
    
    # 2. get_airline_detail() 테스트
    print("\n[2] get_airline_detail() 호출:")
    detail = await airline_service.get_airline_detail(test_airline_code)
    
    if detail:
        print(f"  ✓ 항공사 이름: {detail.name}")
        print(f"  ✓ 총 리뷰 수: {detail.total_reviews}개")
        print(f"  ✓ 전체 평점: {detail.overall_rating}")
        print(f"  ✓ 카테고리별 평균 평점:")
        for category, rating in detail.average_ratings.items():
            print(f"      - {category}: {rating}")
    else:
        print("  ✗ 항공사를 찾을 수 없습니다.")
    
    # 3. 여러 항공사 샘플 확인
    print("\n[3] 여러 항공사 샘플 확인:")
    print("-" * 80)
    
    sample_airlines = ["KE", "OZ", "7C", "AA", "SQ"]
    
    for airline_code in sample_airlines:
        stats = await airline_service.get_airline_statistics(airline_code)
        if stats:
            print(f"\n{stats.airlineName} ({airline_code}):")
            print(f"  - 리뷰: {stats.totalReviews}개")
            print(f"  - 평점: {stats.overallRating}")
        else:
            print(f"\n{airline_code}: 데이터 없음")
    
    print("\n" + "=" * 80)
    print("테스트 완료!")
    print("=" * 80)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
