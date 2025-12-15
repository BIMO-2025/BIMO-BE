"""
대한항공 리뷰에 무작위 이미지 추가
기존 30개 리뷰에 0-3개의 이미지 URL 추가
"""
import asyncio
import random
from app.core.firebase import FirebaseService


# 항공 관련 무작위 이미지 URL (Unsplash에서 항공 관련 이미지)
SAMPLE_IMAGES = [
    "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=800",  # 비행기 날개
    "https://images.unsplash.com/photo-1464037866556-6812c9d1c72e?w=800",  # 기내식
    "https://images.unsplash.com/photo-1488085061387-422e29b40080?w=800",  # 기내 좌석
    "https://images.unsplash.com/photo-1583771132515-d06e77c75879?w=800",  # 창밖 풍경
    "https://images.unsplash.com/photo-1569154243417-7b0394fa2dc1?w=800",  # 비행기 외부
    "https://images.unsplash.com/photo-1544016768-982d1554f0b9?w=800",  # 승무원
    "https://images.unsplash.com/photo-1474302770737-173ee21bab63?w=800",  # 수하물
    "https://images.unsplash.com/photo-1569065095922-7558991d43e5?w=800",  # 공항
    "https://images.unsplash.com/photo-1556388158-158ea5ccacbd?w=800",  # 기내 엔터테인먼트
    "https://images.unsplash.com/photo-1583771131548-49b1b8791902?w=800",  # 일등석
    "https://images.unsplash.com/photo-1542296332-2e4473faf563?w=800",  # 비즈니스석
    "https://images.unsplash.com/photo-1521321205814-9d673c65c167?w=800",  # 공항 라운지
]


async def add_images_to_reviews():
    """대한항공 리뷰에 무작위 이미지 추가"""
    print("=" * 80)
    print("대한항공 리뷰에 이미지 추가 시작")
    print("=" * 80)
    
    # Firebase 초기화
    firebase = FirebaseService()
    firebase.initialize()
    db = firebase.db
    
    reviews_collection = db.collection("reviews")
    
    # 대한항공 리뷰 조회
    print("\n대한항공(KE) 리뷰 조회 중...")
    ke_reviews_query = reviews_collection.where("airlineCode", "==", "KE")
    ke_reviews = list(ke_reviews_query.stream())
    
    print(f"✓ 총 {len(ke_reviews)}개 리뷰 발견")
    
    if len(ke_reviews) == 0:
        print("리뷰가 없습니다!")
        return
    
    # 각 리뷰에 무작위로 0-3개의 이미지 추가
    print("\n이미지 추가 중...")
    updated_count = 0
    
    for doc in ke_reviews:
        review_data = doc.to_dict()
        
        # 무작위로 0-3개 선택
        num_images = random.randint(0, 3)
        
        if num_images > 0:
            # 무작위 이미지 선택
            selected_images = random.sample(SAMPLE_IMAGES, num_images)
            
            # imageUrls 필드 업데이트
            doc.reference.update({
                "imageUrls": selected_images
            })
            
            updated_count += 1
            print(f"  ✓ 리뷰 {doc.id}: {num_images}개 이미지 추가")
        else:
            # 빈 리스트로 설정
            doc.reference.update({
                "imageUrls": []
            })
            print(f"  - 리뷰 {doc.id}: 이미지 없음")
    
    print("\n" + "=" * 80)
    print(f"✓ 완료! 총 {updated_count}/{len(ke_reviews)}개 리뷰에 이미지 추가됨")
    print("=" * 80)
    
    # 통계 출력
    print("\n[통계]")
    ke_reviews_after = list(ke_reviews_query.stream())
    image_counts = {0: 0, 1: 0, 2: 0, 3: 0}
    
    for doc in ke_reviews_after:
        data = doc.to_dict()
        num_images = len(data.get("imageUrls", []))
        image_counts[num_images] += 1
    
    print(f"이미지 0개: {image_counts[0]}개 리뷰")
    print(f"이미지 1개: {image_counts[1]}개 리뷰")
    print(f"이미지 2개: {image_counts[2]}개 리뷰")
    print(f"이미지 3개: {image_counts[3]}개 리뷰")


if __name__ == "__main__":
    asyncio.run(add_images_to_reviews())
