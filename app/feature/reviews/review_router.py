from typing import List
from fastapi import APIRouter, Depends, Header
from app.feature.reviews.review_service import ReviewService
from app.feature.reviews.models import Review, ReviewCreate

router = APIRouter(prefix="/reviews", tags=["reviews"])

def get_review_service():
    return ReviewService()

async def get_current_user_id(authorization: str = Header(None)) -> str:
    if not authorization:
        return "demo_user_123"
    token = authorization.replace("Bearer ", "")
    return token.replace("demo_token_", "")

@router.post("", response_model=Review)
async def create_review(
    review_data: ReviewCreate,
    user_id: str = Depends(get_current_user_id),
    service: ReviewService = Depends(get_review_service)
):
    """리뷰 작성"""
    return await service.create_review(user_id, review_data)

@router.get("/airlines/{airline_id}", response_model=List[Review])
async def get_airline_reviews(
    airline_id: str,
    service: ReviewService = Depends(get_review_service)
):
    """항공사별 리뷰 조회"""
    return await service.get_airline_reviews(airline_id)

@router.get("/me", response_model=List[Review])
async def get_my_reviews(
    user_id: str = Depends(get_current_user_id),
    service: ReviewService = Depends(get_review_service)
):
    """내 리뷰 조회"""
    return await service.get_my_reviews(user_id)
