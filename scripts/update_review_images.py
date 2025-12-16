"""
리뷰에 랜덤한 항공기 이미지를 추가하는 스크립트
"""

import random
from app.core.firebase import db

# 실제 항공기 관련 이미지 URL 리스트 (무료 이미지 사이트에서 가져온 URL들)
AIRPLANE_IMAGES = [
    "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=800",  # 비행기 창문
    "https://images.unsplash.com/photo-1464037866556-6812c9d1c72e?w=800",  # 비행기 날개
    "https://images.unsplash.com/photo-1583922028872-6d5ede5a70e9?w=800",  # 비행기 내부
    "https://images.unsplash.com/photo-1556388158-158ea5ccacbd?w=800",  # 기내식
    "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=800",  # 비행기 좌석
    "https://images.unsplash.com/photo-1569629743817-70d8db6c323b?w=800",  # 비행기 외부
    "https://images.unsplash.com/photo-1488085061387-422e29b40080?w=800",  # 공항
    "https://images.unsplash.com/photo-1589308078059-be1415eab4c3?w=800",  # 기내
    "https://images.unsplash.com/photo-1542296332-2e4473faf563?w=800",  # 비행기 엔진
    "https://images.unsplash.com/photo-1583922028872-6d5ede5a70e9?w=800",  # 승무원
    "https://images.unsplash.com/photo-1565514158740-64d5e8b1dae8?w=800",  # 창밖 풍경
    "https://images.unsplash.com/photo-1520483601560-4b4d5b2e2b0b?w=800",  # 일몰 비행
    "https://images.unsplash.com/photo-1474302770737-173ee21bab63?w=800",  # 비행기 조종석
    "https://images.unsplash.com/photo-1528127269322-539801943592?w=800",  # 기내 엔터테인먼트
    "https://images.unsplash.com/photo-1519915212116-7cfef71f1d3e?w=800",  # 비행기 이륙
]


def update_review_images():
    """
    모든 리뷰에 랜덤한 개수(0-3개)의 실제 이미지를 추가합니다.
    """
    reviews_collection = db.collection("reviews")
    
    # 모든 리뷰 조회
    docs = list(reviews_collection.stream())
    
    print(f"총 {len(docs)}개의 리뷰를 업데이트합니다...")
    
    updated_count = 0
    
    for doc in docs:
        review_data = doc.to_dict()
        
        # 랜덤하게 0~3개의 이미지 선택
        num_images = random.randint(0, 3)
        
        if num_images > 0:
            # 랜덤 이미지 선택
            selected_images = random.sample(AIRPLANE_IMAGES, num_images)
            
            # imageUrls 필드 업데이트
            doc.reference.update({
                "imageUrls": selected_images
            })
            
            updated_count += 1
            print(f"✓ 리뷰 {doc.id}: {num_images}개 이미지 추가")
        else:
            # 이미지 없음
            doc.reference.update({
                "imageUrls": []
            })
            print(f"  리뷰 {doc.id}: 이미지 없음")
    
    print(f"\n완료! 총 {updated_count}개의 리뷰에 이미지가 추가되었습니다.")


if __name__ == "__main__":
    print("=== 리뷰 이미지 업데이트 시작 ===\n")
    update_review_images()
    print("\n=== 완료 ===")
