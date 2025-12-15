"""
대한항공(KE) 상세 리뷰 데이터 삽입 스크립트
한글 100자 이상의 상세한 리뷰 텍스트 포함
"""
import os
import sys
import asyncio
import random
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from app.core.firebase import FirebaseService

# 대한항공 상세 리뷰 템플릿 (최소 100자 이상)
KE_REVIEW_TEMPLATES = {
    "positive": [
        "최석은 아주미리비행이었는데 남편이랑 둘만이 여행이에요 좌석은 이코노미인데 넓고 다리가 진짜 넓어서 불편함 없이 잘 다녀왔고 줄꽈리는 것 같은이 많짜 가방이카 마라도 막을 다 고려해야 뭐든 할수 있어요 기내 수리 보급시 나눔 후라이어와 14시간 내내 고생한 서무라고 그래서 여저 조차도 못받은 혹했은 이런 비행 별 달말 먼 훌륭한 서비스를 받았습니다.",
        
        "인천에서 파리까지 비즈니스석을 이용했는데요 정말 최고의 경험이었습니다 좌석이 완전히 눕혀져서 장거리 비행임에도 푹 쉬어갈 수 있었고 승무원분들이 정말 친절하게 응대해주셨어요 기내식은 한식과 양식 중 선택할 수 있었는데 둘 다 레스토랑 수준의 퀄리티였습니다 특히 비빔밥이 정말 맛있었어요 엔터테인먼트 시스템도 최신 영화와 드라마가 다양하게 준비되어 있어서 지루할 틈이 없었습니다 다음에도 꼭 대한항공을 이용하고 싶어요",
        
        "도쿄 하네다 공항으로 가는 단거리 노선이었지만 서비스가 정말 훌륭했습니다 체크인부터 탑승까지 모든 과정이 매끄러웠고 기내에서도 승무원분들이 세심하게 신경써주셨어요 좌석 간격도 적당해서 불편함이 없었고 기내식으로 나온 샌드위치와 음료도 맛있었습니다 정시 출발하고 정시 도착해서 일정 관리하기에도 좋았어요 깨끗한 기내 환경과 친절한 서비스로 편안한 여행이 되었습니다",
        
        "뉴욕까지 장거리 비행이었는데 프리미엄 이코노미를 선택했습니다 일반석보다 좌석이 넓고 리클라인도 더 많이 되어서 편안했어요 발 받침대와 헤드레스트 조절도 가능해서 좋았습니다 기내식이 정말 다양하게 나왔는데 특히 한식 메뉴가 훌륭했어요 개인 모니터도 크고 선명해서 영화 보기에 좋았습니다 무엇보다 승무원분들이 계속 음료와 간식을 챙겨주셔서 감동이었어요 가격 대비 정말 만족스러운 비행이었습니다",
        
        "프랑크푸르트행 비행기를 탔는데 전반적으로 완벽한 경험이었습니다 라운지부터 시작해서 기내 서비스까지 모든 것이 최고 수준이었어요 좌석은 넓고 푹신했으며 청결 상태도 완벽했습니다 기내식은 세 번 제공되었는데 매 끼니마다 퀄리티가 높았어요 특히 아침 식사로 나온 죽이 정말 맛있었습니다 와이파이도 잘 터져서 업무도 처리할 수 있었고 승무원분들이 항상 웃으면서 친절하게 대해주셔서 기분 좋은 여행이었습니다",
    ],
    
    "neutral": [
        "LA까지 가는 비행이었는데 전반적으로 무난한 편이었습니다 좌석은 조금 좁다고 느껴졌지만 견딜만한 수준이었고 기내식은 평범했어요 양은 충분했지만 맛은 기대했던 것보다는 조금 아쉬웠습니다 엔터테인먼트 시스템은 잘 작동했고 영화 선택지도 많았어요 승무원분들은 친절하셨지만 바쁘셔서 추가 요청했을 때 조금 기다려야 했습니다 가격을 생각하면 합리적인 선택이었다고 봅니다",
        
        "베이징행 단거리 노선을 이용했습니다 특별히 나쁘거나 좋은 점은 없었어요 좌석은 평범했고 기내 서비스도 표준적인 수준이었습니다 기내식은 간단한 샌드위치와 음료가 제공되었는데 맛은 그저 그랬어요 다만 정시에 출발하고 도착해서 일정 관리에는 문제가 없었습니다 전반적으로 평균적인 비행 경험이었다고 생각합니다 다음에도 가격이 적당하면 이용할 의향은 있어요",
        
        "시드니까지의 장거리 비행이었습니다 좌석이 조금 불편했지만 담요와 베개가 제공되어서 어느 정도 해소되었어요 기내식은 세 번 나왔는데 첫 번째 식사는 괜찮았지만 나머지는 평범했습니다 엔터테인먼트는 다양했지만 개인 모니터가 작아서 조금 아쉬웠어요 승무원분들은 친절했지만 바빠 보였습니다 전체적으로 가격 대비 적절한 수준의 서비스였다고 봅니다",
    ],
    
    "negative": [
        "샌프란시스코행 비행기였는데 좌석이 정말 좁아서 12시간 내내 불편했습니다 다리를 제대로 펼 수 없어서 계속 자세를 바꿔야 했어요 기내식도 기대 이하였고 특히 메인 요리가 너무 짰습니다 승무원분들도 바빠 보이셔서 요청 사항에 응대가 늦었어요 개인 모니터 화질도 좋지 않았고 리모컨 반응도 느렸습니다 장거리 비행치고는 전반적으로 만족도가 낮았어요 다음에는 다른 항공사를 고려해볼 것 같습니다",
        
        "방콕행 비행기를 탔는데 여러모로 아쉬운 점이 많았습니다 우선 출발이 1시간 가까이 지연되었는데 안내가 부족했어요 기내에 들어가니 에어컨이 잘 안 나와서 덥고 답답했습니다 좌석도 청결 상태가 좋지 않았고 기내식은 선택지가 적었어요 승무원분들의 서비스도 다소 무뚝뚝하게 느껴졌습니다 전반적으로 가격 대비 만족도가 낮은 비행이었다고 생각합니다",
    ]
}

# 노선 (대한항공 주요 노선)
KE_ROUTES = [
    "ICN-JFK", "ICN-LAX", "ICN-SFO", "ICN-SEA", "ICN-YVR",  # 북미
    "ICN-CDG", "ICN-LHR", "ICN-FRA", "ICN-AMS", "ICN-FCO",  # 유럽
    "ICN-NRT", "ICN-HND", "ICN-KIX", "ICN-FUK", "ICN-CTS",  # 일본
    "ICN-SYD", "ICN-AKL",  # 오세아니아
    "ICN-BKK", "ICN-SIN", "ICN-MNL", "ICN-HKG",  # 동남아
]

SEAT_CLASSES = ["이코노미", "프리미엄 이코노미", "비즈니스", "퍼스트"]

USER_NICKNAMES = [
    "여행조아", "항공마니아", "BIMO유저", "세계여행중", "스카이러버",
    "트래블러K", "비행기타는사람", "여행기록", "마일리지수집가", "하늘여행",
]


def generate_ratings():
    """평점 생성"""
    seat_comfort = random.randint(2, 5)
    inflight_meal = random.randint(2, 5)
    service = random.randint(3, 5)
    cleanliness = random.randint(3, 5)
    check_in = random.randint(3, 5)
    
    overall = round((seat_comfort + inflight_meal + service + cleanliness + check_in) / 5, 1)
    
    return {
        "seatComfort": seat_comfort,
        "inflightMeal": inflight_meal,
        "service": service,
        "cleanliness": cleanliness,
        "checkIn": check_in
    }, overall


def get_review_text(overall_rating):
    """평점에 따라 리뷰 선택"""
    if overall_rating >= 4.0:
        category = "positive"
    elif overall_rating >= 3.0:
        category = "neutral"
    else:
        category = "negative"
    
    return random.choice(KE_REVIEW_TEMPLATES[category])


def generate_ke_review(user_id_suffix):
    """대한항공 리뷰 생성"""
    ratings, overall_rating = generate_ratings()
    route = random.choice(KE_ROUTES)
    seat_class = random.choice(SEAT_CLASSES)
    
    # 최근 1년 내 날짜
    days_ago = random.randint(0, 365)
    created_at = datetime.now(timezone.utc) - timedelta(days=days_ago)
    
    review = {
        "userId": f"ke_user_{user_id_suffix:04d}",
        "userNickname": random.choice(USER_NICKNAMES),
        "airlineCode": "KE",
        "airlineName": "대한항공",
        "route": route,
        "flightNumber": f"KE{random.randint(1, 999):03d}",
        "seatClass": seat_class,
        "imageUrl": None,
        "ratings": ratings,
        "overallRating": overall_rating,
        "text": get_review_text(overall_rating),
        "isVerified": random.random() < 0.8,  # 80% 인증
        "likes": random.randint(5, 50),
        "createdAt": created_at,
    }
    
    return review


async def main():
    """메인 실행"""
    print("=" * 80)
    print("대한항공(KE) 상세 리뷰 데이터 삽입")
    print("=" * 80)
    
    # Firebase 초기화
    firebase_service = FirebaseService()
    firebase_service.initialize()
    db = firebase_service.db
    
    reviews_collection = db.collection("reviews")
    
    # 대한항공 리뷰 20개 생성
    num_reviews = 20
    print(f"\n대한항공 리뷰 {num_reviews}개 생성 중...")
    
    batch = db.batch()
    
    for i in range(1, num_reviews + 1):
        review_data = generate_ke_review(i)
        review_ref = reviews_collection.document()
        batch.set(review_ref, review_data)
        print(f"  [{i}/{num_reviews}] 리뷰 생성: {review_data['route']} | {review_data['seatClass']} | 평점 {review_data['overallRating']}")
    
    # 배치 커밋
    print("\nFirebase에 저장 중...")
    batch.commit()
    
    print("\n" + "=" * 80)
    print(f"✓ 대한항공 리뷰 {num_reviews}개 삽입 완료!")
    print("=" * 80)
    
    # 검증
    ke_reviews = list(reviews_collection.where("airlineCode", "==", "KE").stream())
    print(f"\n[검증] 대한항공 총 리뷰 수: {len(ke_reviews)}개")


if __name__ == "__main__":
    asyncio.run(main())
