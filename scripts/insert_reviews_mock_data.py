"""
항공사별 리뷰 목데이터 삽입 스크립트
86개 항공사 각각에 10개씩 리뷰 데이터 삽입 (총 860개)
"""
import os
import sys
import asyncio
import random
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from app.core.firebase import FirebaseService

# 리뷰 템플릿 데이터
REVIEW_TEMPLATES = {
    "positive": [
        "좌석이 정말 편안했고 승무원들의 서비스가 훌륭했습니다. 기내식도 맛있었어요!",
        "깨끗하고 안전한 비행이었습니다. 체크인 과정도 빠르고 효율적이었어요.",
        "전반적으로 만족스러운 여행이었습니다. 다음에도 이용하고 싶습니다.",
        "승무원분들이 정말 친절하셨고, 기내 엔터테인먼트 시스템도 좋았습니다.",
        "정시 출발과 도착으로 일정 관리가 편했습니다. 추천합니다!",
        "비즈니스석 라운지가 훌륭했고, 기내식 퀄리티가 매우 좋았습니다.",
        "장거리 비행이었지만 편안하게 잘 쉬어갈 수 있었습니다.",
        "체크인부터 도착까지 모든 과정이 매끄러웠습니다. 만족합니다.",
    ],
    "neutral": [
        "평범한 비행이었습니다. 특별히 좋거나 나쁘지 않았어요.",
        "가격 대비 괜찮은 서비스였습니다. 기내식은 보통이었어요.",
        "전반적으로 무난했습니다. 좌석은 조금 좁았지만 견딜만 했어요.",
        "서비스는 평균 수준이었고, 특별한 불편함은 없었습니다.",
        "기대했던 것만큼은 아니었지만 나쁘지 않았습니다.",
        "가격을 생각하면 합리적인 선택이었습니다.",
    ],
    "negative": [
        "좌석이 너무 좁아서 불편했습니다. 기내식도 기대 이하였어요.",
        "지연이 심했고 안내가 부족했습니다. 아쉬운 경험이었어요.",
        "승무원의 서비스가 불친절했고 청결 상태도 좋지 않았습니다.",
        "체크인 과정이 너무 복잡하고 오래 걸렸습니다.",
        "기내 온도가 너무 덥거나 추워서 불편했습니다.",
    ]
}

# 항공편 목록 (자주 사용되는 주요 노선)
POPULAR_ROUTES = [
    "ICN-NRT", "ICN-HND", "ICN-KIX", "ICN-FUK", "ICN-CTS",  # 일본
    "ICN-PEK", "ICN-PVG", "ICN-CAN", "ICN-SHA", "ICN-XIY",  # 중국
    "ICN-BKK", "ICN-SIN", "ICN-MNL", "ICN-HKG", "ICN-TPE",  # 동남아시아
    "ICN-LAX", "ICN-JFK", "ICN-SFO", "ICN-SEA", "ICN-YVR",  # 북미
    "ICN-CDG", "ICN-LHR", "ICN-FRA", "ICN-AMS", "ICN-FCO",  # 유럽
    "ICN-SYD", "ICN-AKL", "ICN-BNE",  # 오세아니아
    "GMP-HND", "GMP-SHA", "GMP-PEK",  # 김포공항
]

# 좌석 등급
SEAT_CLASSES = ["이코노미", "프리미엄 이코노미", "비즈니스", "퍼스트"]

# 사용자 닉네임 목록
USER_NICKNAMES = [
    "여행러버", "하늘여행자", "비행기매니아", "세계여행가", "BIMO",
    "트래블러", "항공덕후", "여행중독", "마일리지왕", "스카이워커",
    "구름위의산책", "여행일기", "세계일주꿈나무", "플라잉맨", "여행자K",
    "하늘을나는새", "여행메이트", "비즈니스맨", "백패커", "여행블로거",
]


def generate_ratings():
    """무작위 평점 생성"""
    seat_comfort = random.randint(1, 5)
    inflight_meal = random.randint(1, 5)
    service = random.randint(1, 5)
    cleanliness = random.randint(1, 5)
    check_in = random.randint(1, 5)
    
    overall = round((seat_comfort + inflight_meal + service + cleanliness + check_in) / 5, 1)
    
    return {
        "seatComfort": seat_comfort,
        "inflightMeal": inflight_meal,
        "service": service,
        "cleanliness": cleanliness,
        "checkIn": check_in
    }, overall


def get_review_text(overall_rating):
    """평점에 따라 적절한 리뷰 텍스트 선택"""
    if overall_rating >= 4.0:
        category = "positive"
    elif overall_rating >= 3.0:
        category = "neutral"
    else:
        category = "negative"
    
    return random.choice(REVIEW_TEMPLATES[category])


def generate_mock_review(airline_code, airline_name, user_id_suffix):
    """단일 목데이터 리뷰 생성"""
    ratings, overall_rating = generate_ratings()
    route = random.choice(POPULAR_ROUTES)
    seat_class = random.choice(SEAT_CLASSES)
    
    # 최근 1년 내 무작위 날짜 생성
    days_ago = random.randint(0, 365)
    created_at = datetime.now(timezone.utc) - timedelta(days=days_ago)
    
    # 좋아요 수 (0~100 사이)
    likes = random.randint(0, 100)
    
    # 인증 여부 (70% 확률로 인증됨)
    is_verified = random.random() < 0.7
    
    review = {
        "userId": f"user_{user_id_suffix:04d}",
        "userNickname": random.choice(USER_NICKNAMES),
        "airlineCode": airline_code,
        "airlineName": airline_name,
        "route": route,
        "flightNumber": f"{airline_code}{random.randint(100, 999)}",
        "seatClass": seat_class,
        "imageUrl": None,  # 목데이터에서는 이미지 없음
        "ratings": ratings,
        "overallRating": overall_rating,
        "text": get_review_text(overall_rating),
        "isVerified": is_verified,
        "likes": likes,
        "createdAt": created_at,
    }
    
    return review


async def main():
    """메인 실행 함수"""
    print("=" * 80)
    print("항공사별 리뷰 목데이터 삽입 시작")
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
    
    if len(airlines_docs) != 86:
        print(f"⚠️  경고: 예상 항공사 수(86개)와 다릅니다. 실제: {len(airlines_docs)}개")
        response = input("계속 진행하시겠습니까? (y/n): ")
        if response.lower() != 'y':
            print("작업이 취소되었습니다.")
            return
    
    # 2. 각 항공사별로 리뷰 10개씩 생성 및 삽입
    print("\n[2단계] 리뷰 데이터 생성 및 삽입 중...")
    
    total_reviews_inserted = 0
    user_id_counter = 1
    
    for idx, airline_doc in enumerate(airlines_docs, 1):
        airline_code = airline_doc.id
        airline_data = airline_doc.to_dict()
        airline_name = airline_data.get("airlineName", airline_code)
        
        print(f"\n진행: [{idx}/{len(airlines_docs)}] {airline_name} ({airline_code})")
        
        # 각 항공사에 대해 10개의 리뷰 생성
        batch = db.batch()
        reviews_for_this_airline = []
        
        for i in range(10):
            review_data = generate_mock_review(airline_code, airline_name, user_id_counter)
            user_id_counter += 1
            
            # reviews 컬렉션에 문서 추가
            review_ref = reviews_collection.document()
            batch.set(review_ref, review_data)
            reviews_for_this_airline.append(review_data)
        
        # 배치 커밋
        batch.commit()
        total_reviews_inserted += 10
        
        print(f"  ✓ 10개 리뷰 삽입 완료 (전체 진행: {total_reviews_inserted}개)")
    
    # 3. 결과 출력
    print("\n" + "=" * 80)
    print("리뷰 목데이터 삽입 완료!")
    print("=" * 80)
    print(f"총 항공사 수: {len(airlines_docs)}개")
    print(f"총 삽입된 리뷰: {total_reviews_inserted}개")
    print(f"항공사당 리뷰 수: 10개")
    print("=" * 80)
    
    # 4. 검증: 첫 번째 항공사의 리뷰 개수 확인
    if airlines_docs:
        first_airline_code = airlines_docs[0].id
        first_airline_name = airlines_docs[0].to_dict().get("airlineName", first_airline_code)
        
        reviews_query = reviews_collection.where("airlineCode", "==", first_airline_code)
        reviews_count = len(list(reviews_query.stream()))
        
        print(f"\n[검증] {first_airline_name} ({first_airline_code})의 리뷰 개수: {reviews_count}개")


if __name__ == "__main__":
    asyncio.run(main())
