"""
종합 데이터베이스 시딩 스크립트
myFlights, reviews, airlines 데이터를 생성합니다.
"""

import asyncio
import sys
import os
import random
from datetime import datetime, timedelta, timezone

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.firebase import db

# Mock 사용자 데이터
MOCK_USERS = [
    {"id": "user1", "nickname": "BIMO"},
    {"id": "user2", "nickname": "Traveler"},
    {"id": "user3", "nickname": "SkyExplorer"},
    {"id": "user4", "nickname": "Wings"},
    {"id": "user5", "nickname": "JetSet"},
]

# 항공사 코드 및 이름
AIRLINES = [
    {"code": "KE", "name": "대한항공", "name_en": "Korean Air", "country": "대한민국", "alliance": "SkyTeam", "hub": "ICN"},
    {"code": "OZ", "name": "아시아나항공", "name_en": "Asiana Airlines", "country": "대한민국", "alliance": "Star Alliance", "hub": "ICN"},
    {"code": "JL", "name": "일본항공", "name_en": "Japan Airlines", "country": "일본", "alliance": "oneworld", "hub": "NRT"},
    {"code": "NH", "name": "전일본공수", "name_en": "All Nippon Airways", "country": "일본", "alliance": "Star Alliance", "hub": "NRT"},
    {"code": "SQ", "name": "싱가포르항공", "name_en": "Singapore Airlines", "country": "싱가포르", "alliance": "Star Alliance", "hub": "SIN"},
    {"code": "EK", "name": "에미레이트항공", "name_en": "Emirates", "country": "아랍에미리트", "alliance": None, "hub": "DXB"},
    {"code": "QR", "name": "카타르항공", "name_en": "Qatar Airways", "country": "카타르", "alliance": "oneworld", "hub": "DOH"},
    {"code": "DL", "name": "델타항공", "name_en": "Delta Air Lines", "country": "미국", "alliance": "SkyTeam", "hub": "ATL"},
    {"code": "AA", "name": "아메리칸항공", "name_en": "American Airlines", "country": "미국", "alliance": "oneworld", "hub": "DFW"},
    {"code": "UA", "name": "유나이티드항공", "name_en": "United Airlines", "country": "미국", "alliance": "Star Alliance", "hub": "ORD"},
    {"code": "AF", "name": "에어프랑스", "name_en": "Air France", "country": "프랑스", "alliance": "SkyTeam", "hub": "CDG"},
    {"code": "KL", "name": "KLM", "name_en": "KLM Royal Dutch Airlines", "country": "네덜란드", "alliance": "SkyTeam", "hub": "AMS"},
    {"code": "LH", "name": "루프트한자", "name_en": "Lufthansa", "country": "독일", "alliance": "Star Alliance", "hub": "FRA"},
    {"code": "BA", "name": "영국항공", "name_en": "British Airways", "country": "영국", "alliance": "oneworld", "hub": "LHR"},
    {"code": "QF", "name": "콴타스", "name_en": "Qantas", "country": "호주", "alliance": "oneworld", "hub": "SYD"},
]

# 주요 노선
ROUTES = [
    "ICN-JFK", "ICN-LAX", "ICN-NRT", "ICN-HKG", "ICN-SIN",
    "JFK-LHR", "JFK-CDG", "LAX-NRT", "NRT-SIN", "HKG-BKK",
    "SIN-BKK", "BKK-DXB", "DXB-LHR", "LHR-CDG", "CDG-FRA",
]

# 리뷰 텍스트 템플릿 (더 다양하게 확장)
REVIEW_TEXTS = [
    "좌석이 매우 편안했고, 기내식도 맛있었습니다. 승무원 서비스가 친절해서 좋은 경험이었어요.",
    "가격 대비 만족스러운 항공편이었습니다. 다만 좌석 공간이 좀 좁았어요.",
    "체크인 과정이 빠르고 편리했습니다. 기내 서비스도 훌륭했어요.",
    "좌석은 편안했지만 기내식이 아쉬웠습니다. 다음에는 다른 메뉴를 시도해볼 예정이에요.",
    "전반적으로 만족스러운 항공편이었습니다. 특히 승무원의 친절한 서비스가 인상적이었어요.",
    "비행 시간이 길었는데 좌석이 편안해서 편안하게 지낼 수 있었습니다.",
    "기내 청결도가 뛰어났고, 서비스도 좋았어요. 추천합니다!",
    "가격이 조금 비싸긴 하지만, 서비스 품질을 생각하면 합리적이에요.",
    "좌석이 이코노미인데 생각보다 넓어서 편했습니다. 다만 기내식이 좀 아쉬웠어요.",
    "14시간 비행이었는데 승무원 분들이 정말 친절하게 도와주셔서 좋았습니다.",
    "인천에서 파리까지 직항이어서 편했어요. 다음에도 이 항공사 이용할 예정입니다.",
    "체크인할 때 시간이 좀 걸렸지만, 기내 서비스는 만족스러웠습니다.",
    "좌석 공간이 좁긴 했지만 가격 대비로는 괜찮았어요.",
    "기내식 메뉴가 다양하고 맛있었습니다. 특히 디저트가 좋았어요.",
    "청결도가 아쉬웠지만, 승무원 서비스는 정말 훌륭했습니다.",
    "지연 없이 정확하게 출발하고 도착해서 만족스러웠어요.",
    "비즈니스 클래스로 이용했는데, 라운지와 기내 서비스 모두 훌륭했습니다.",
    "가족 여행으로 이용했는데, 아이들을 배려해주는 서비스가 좋았어요.",
    "좌석이 좀 오래된 느낌이었지만, 전반적으로 괜찮은 항공편이었습니다.",
    "기내 Wi-Fi가 제공되어서 업무를 할 수 있어서 좋았어요.",
]

# 좌석 등급
SEAT_CLASSES = ["이코노미", "프리미엄 이코노미", "비즈니스", "퍼스트"]

# 항공편 번호 템플릿
FLIGHT_NUMBER_TEMPLATES = {
    "KE": "KE", "OZ": "OZ", "JL": "JL", "NH": "NH", "SQ": "SQ",
    "EK": "EK", "QR": "QR", "DL": "DL", "AA": "AA", "UA": "UA",
    "AF": "AF", "KL": "KL", "LH": "LH", "BA": "BA", "QF": "QF",
}

# 리뷰 이미지 URL (예시)
IMAGE_URLS = [
    "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=800",
    "https://images.unsplash.com/photo-1586348943529-beaae6c28db9?w=800",
    "https://images.unsplash.com/photo-1513506003901-1e6a229e2d15?w=800",
    None,  # 이미지 없는 리뷰도 포함
]


def generate_random_datetime(days_ago_min: int = 0, days_ago_max: int = 365) -> datetime:
    """랜덤 날짜/시간 생성"""
    days_ago = random.randint(days_ago_min, days_ago_max)
    hours = random.randint(0, 23)
    minutes = random.randint(0, 59)
    dt = datetime.now(timezone.utc) - timedelta(days=days_ago, hours=hours, minutes=minutes)
    return dt


def calculate_overall_rating(ratings: dict) -> float:
    """전체 평점 계산"""
    total = sum(ratings.values())
    return round(total / len(ratings), 1)


async def seed_users():
    """Mock 사용자 데이터 생성"""
    print("👤 사용자 데이터 생성 중...")
    users_collection = db.collection("users")
    
    for user in MOCK_USERS:
        user_ref = users_collection.document(user["id"])
        doc = user_ref.get()
        
        if not doc.exists:
            user_ref.set({
                "nickname": user["nickname"],
                "sleepPatternStart": datetime(2025, 1, 1, 23, 0, 0, tzinfo=timezone.utc),
                "sleepPatternEnd": datetime(2025, 1, 2, 7, 0, 0, tzinfo=timezone.utc),
                "createdAt": datetime.now(timezone.utc),
            })
            print(f"  + 사용자 생성: {user['nickname']} ({user['id']})")
        else:
            print(f"  ✓ 사용자 존재: {user['nickname']} ({user['id']})")


async def seed_my_flights():
    """Mock 비행 기록 생성"""
    print("\n✈️ 비행 기록 생성 중...")
    
    flight_count = 0
    
    for user in MOCK_USERS:
        user_id = user["id"]
        my_flights_collection = db.collection("users").document(user_id).collection("myFlights")
        
        # 각 사용자당 5-10개의 비행 기록 생성
        num_flights = random.randint(5, 10)
        
        for i in range(num_flights):
            airline = random.choice(AIRLINES)
            route = random.choice(ROUTES)
            departure_time = generate_random_datetime(days_ago_min=0, days_ago_max=180)
            flight_duration_hours = random.randint(2, 14)
            arrival_time = departure_time + timedelta(hours=flight_duration_hours)
            
            # 과거 비행은 completed, 미래 비행은 scheduled
            status = "completed" if departure_time < datetime.now(timezone.utc) else "scheduled"
            
            flight_data = {
                "flightNumber": f"{airline['code']}{random.randint(100, 9999)}",
                "airlineCode": airline["code"],
                "departureTime": departure_time,
                "arrivalTime": arrival_time,
                "status": status,
                "reviewId": None,  # 나중에 리뷰 생성 시 연결
            }
            
            doc_ref = my_flights_collection.document()
            doc_ref.set(flight_data)
            flight_count += 1
    
    print(f"  ✅ 총 {flight_count}개의 비행 기록 생성 완료")


async def seed_reviews_and_airlines():
    """리뷰 및 항공사 집계 데이터 생성"""
    print("\n📝 리뷰 및 항공사 집계 데이터 생성 중...")
    
    reviews_collection = db.collection("reviews")
    airlines_collection = db.collection("airlines")
    
    # 항공사별 집계 데이터 초기화
    airline_stats = {}
    for airline in AIRLINES:
        hub = airline.get("hub", "")
        code = airline["code"]
        logo_url = f"https://pics.avs.io/200/200/{code}.png"
        images = [
            logo_url,
            f"https://pics.avs.io/400/200/{code}.png",
            "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=800",
            "https://images.unsplash.com/photo-1586348943529-beaae6c28db9?w=800",
        ]
        
        airline_stats[airline["code"]] = {
            "airlineName": airline["name"],
            "airlineNameEn": airline.get("name_en"),
            "country": airline.get("country", ""),
            "hubAirport": hub,
            "hubAirportName": hub_airport_names.get(hub),
            "alliance": airline.get("alliance"),
            "type": "FSC",
            "operatingClasses": ["이코노미", "프리미엄 이코노미", "비즈니스", "퍼스트"],
            "logoUrl": logo_url,
            "images": images,
            "totalReviews": 0,
            "totalRatingSums": {
                "seatComfort": 0,
                "inflightMeal": 0,
                "service": 0,
                "cleanliness": 0,
                "checkIn": 0,
            },
            "ratingBreakdown": {
                "seatComfort": {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0},
                "inflightMeal": {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0},
                "service": {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0},
                "cleanliness": {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0},
                "checkIn": {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0},
            },
        }
    
    # 리뷰 생성 (각 항공사당 최소 3개 이상, 최대 50개)
    review_count = 0
    
    for airline in AIRLINES:
        # 최소 3개, 최대 50개
        num_reviews = random.randint(3, 50)
        airline_code = airline["code"]
        airline_prefix = FLIGHT_NUMBER_TEMPLATES.get(airline_code, airline_code)
        
        for i in range(num_reviews):
            user = random.choice(MOCK_USERS)
            route = random.choice(ROUTES)
            
            # 랜덤 평점 생성
            ratings = {
                "seatComfort": random.randint(1, 5),
                "inflightMeal": random.randint(1, 5),
                "service": random.randint(1, 5),
                "cleanliness": random.randint(1, 5),
                "checkIn": random.randint(1, 5),
            }
            
            overall_rating = calculate_overall_rating(ratings)
            
            # 항공편 번호 생성 (예: KE901, AF123 등)
            flight_number = f"{airline_prefix}{random.randint(100, 9999)}"
            
            # 좌석 등급
            seat_class = random.choice(SEAT_CLASSES)
            
            # 좋아요 수 (0-100 사이)
            likes = random.randint(0, 100)
            
            # 이미지 URL (약 30% 확률로 이미지 포함)
            image_url = random.choice(IMAGE_URLS) if random.random() < 0.3 else None
            
            # 리뷰 데이터
            review_data = {
                "userId": user["id"],
                "userNickname": user["nickname"],
                "airlineCode": airline_code,
                "airlineName": airline["name"],
                "route": route,
                "flightNumber": flight_number,
                "seatClass": seat_class,
                "imageUrl": image_url,
                "ratings": ratings,
                "overallRating": overall_rating,
                "text": random.choice(REVIEW_TEXTS),
                "isVerified": random.choice([True, False]),  # 일부만 인증된 리뷰
                "likes": likes,
                "createdAt": generate_random_datetime(days_ago_min=0, days_ago_max=90),
            }
            
            # 리뷰 생성
            doc_ref = reviews_collection.document()
            doc_ref.set(review_data)
            review_count += 1
            
            # 집계 데이터 업데이트
            stats = airline_stats[airline_code]
            stats["totalReviews"] += 1
            
            for category, rating in ratings.items():
                stats["totalRatingSums"][category] += rating
                stats["ratingBreakdown"][category][str(rating)] += 1
    
        # 평균 평점 계산 및 항공사 데이터 저장
    print(f"  ✅ 총 {review_count}개의 리뷰 생성 완료")
    print("\n📊 항공사 집계 데이터 저장 중...")
    
    for airline_code, stats in airline_stats.items():
        # 평균 평점 계산
        average_ratings = {}
        for category in ["seatComfort", "inflightMeal", "service", "cleanliness", "checkIn"]:
            if stats["totalReviews"] > 0:
                avg = stats["totalRatingSums"][category] / stats["totalReviews"]
                average_ratings[category] = round(avg, 2)
            else:
                average_ratings[category] = 0.0
        
        # 전체 평균 평점 계산 (카테고리별 평균의 평균)
        if stats["totalReviews"] > 0 and average_ratings:
            overall_rating = round(sum(average_ratings.values()) / len(average_ratings), 2)
        else:
            overall_rating = 0.0
        
        # 항공사 문서 저장 (AirlineSchema 형식)
        airline_ref = airlines_collection.document(airline_code)
        airline_data = {
            "airlineName": stats["airlineName"],
            "airlineNameEn": stats.get("airlineNameEn"),
            "country": stats.get("country", ""),
            "hubAirport": stats.get("hubAirport"),
            "hubAirportName": stats.get("hubAirportName"),
            "alliance": stats.get("alliance"),
            "type": stats.get("type", "FSC"),
            "operatingClasses": stats.get("operatingClasses", []),
            "logoUrl": stats.get("logoUrl"),
            "images": stats.get("images", []),
            "totalReviews": stats["totalReviews"],
            "totalRatingSums": stats["totalRatingSums"],
            "averageRatings": average_ratings,
            "ratingBreakdown": stats["ratingBreakdown"],
            "overallRating": overall_rating,
        }
        
        airline_ref.set(airline_data, merge=True)
        
        print(f"  ✓ {stats['airlineName']} ({airline_code}): {stats['totalReviews']}개 리뷰, 평점 {overall_rating}/5.0")


async def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("🛫 종합 데이터베이스 시딩 시작")
    print("=" * 60)
    
    try:
        await seed_users()
        await seed_my_flights()
        await seed_reviews_and_airlines()
        
        print("\n" + "=" * 60)
        print("✅ 모든 데이터 시딩 완료!")
        print("=" * 60)
        print("\n생성된 데이터:")
        print(f"  - 사용자: {len(MOCK_USERS)}명")
        print(f"  - 항공사: {len(AIRLINES)}개")
        print(f"  - 리뷰: 다수")
        print(f"  - 비행 기록: 다수")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())

