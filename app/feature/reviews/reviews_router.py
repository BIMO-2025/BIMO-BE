"""
리뷰 관련 API 라우터
"""

from fastapi import APIRouter, Query
from typing import Optional

from app.feature.reviews import reviews_schemas, reviews_service

router = APIRouter(
    prefix="/reviews",
    tags=["Reviews"],
    responses={404: {"description": "Not found"}},
)


@router.get("/airline/{airline_code}", response_model=list[reviews_schemas.ReviewSchema])
async def get_airline_reviews(
    airline_code: str,
    limit: int = Query(10, ge=1, le=100, description="조회할 리뷰 개수")
):
    """
    항공사 코드로 리뷰 목록을 조회합니다.
    
    - **airline_code**: 항공사 코드 (예: KE, OZ)
    - **limit**: 조회할 리뷰 개수 (기본값: 10, 최대: 100)
    """
    return await reviews_service.get_reviews_by_airline(airline_code, limit=limit)


@router.get("/{review_id}", response_model=reviews_schemas.ReviewSchema)
async def get_review(review_id: str):
    """
    리뷰 ID로 특정 리뷰를 조회합니다.
    
    - **review_id**: 리뷰 ID
    """
    return await reviews_service.get_review_by_id(review_id)


@router.post("/summarize", response_model=reviews_schemas.ReviewSummaryResponse)
async def summarize_airline_reviews(
    request: reviews_schemas.ReviewSummaryRequest
):
    """
    LLM을 사용하여 항공사 리뷰를 요약합니다.
    
    - **airline_code**: 항공사 코드 (필수)
    - **airline_name**: 항공사 이름 (선택사항)
    - **limit**: 요약에 사용할 리뷰 개수 (기본값: 50, 최대: 100)
    
    LLM이 리뷰들을 분석하여 전체적인 평가, 장점, 단점, 추천 대상을 요약합니다.
    """
    return await reviews_service.get_airline_reviews_summary(
        airline_code=request.airline_code,
        airline_name=request.airline_name
    )


