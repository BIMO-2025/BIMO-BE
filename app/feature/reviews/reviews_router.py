"""
리뷰 관련 API 라우터
"""

from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional

from app.core.deps import get_firebase_service, get_gemini_client
from app.core.firebase import FirebaseService
from app.feature.llm.gemini_client import GeminiClient
from app.feature.reviews.reviews_service import ReviewsService
from app.feature.reviews import reviews_schemas

router = APIRouter(
    prefix="/reviews",
    tags=["Reviews"],
    responses={404: {"description": "Not found"}},
)


def get_reviews_service(
    firebase_service: FirebaseService = Depends(get_firebase_service),
    gemini_client: GeminiClient = Depends(get_gemini_client)
) -> ReviewsService:
    """ReviewsService 의존성 주입"""
    return ReviewsService(
        firebase_service=firebase_service,
        gemini_client=gemini_client
    )


@router.get("/airline/{airline_code}", response_model=list[reviews_schemas.ReviewSchema])
async def get_airline_reviews(
    airline_code: str,
    limit: int = Query(10, ge=1, le=100, description="조회할 리뷰 개수"),
    service: ReviewsService = Depends(get_reviews_service)
):
    """
    항공사 코드로 리뷰 목록을 조회합니다.
    
    - **airline_code**: 항공사 코드 (예: KE, OZ)
    - **limit**: 조회할 리뷰 개수 (기본값: 10, 최대: 100)
    """
    return await service.get_reviews_by_airline(airline_code, limit=limit)


@router.get("/{review_id}", response_model=reviews_schemas.ReviewSchema)
async def get_review(
    review_id: str,
    service: ReviewsService = Depends(get_reviews_service)
):
    """
    리뷰 ID로 특정 리뷰를 조회합니다.
    
    - **review_id**: 리뷰 ID
    """
    return await service.get_review_by_id(review_id)


@router.post("/summarize", response_model=reviews_schemas.ReviewSummaryResponse)
async def summarize_airline_reviews(
    request: reviews_schemas.ReviewSummaryRequest,
    service: ReviewsService = Depends(get_reviews_service)
):
    """
    LLM을 사용하여 항공사 리뷰를 요약합니다.
    
    - **airline_code**: 항공사 코드 (필수)
    - **airline_name**: 항공사 이름 (선택사항)
    - **limit**: 요약에 사용할 리뷰 개수 (기본값: 50, 최대: 100)
    
    LLM이 리뷰들을 분석하여 전체적인 평가, 장점, 단점, 추천 대상을 요약합니다.
    """
    return await service.get_airline_reviews_summary(
        airline_code=request.airline_code,
        airline_name=request.airline_name
    )


@router.get("/detailed/{airline_code}", response_model=reviews_schemas.DetailedReviewsResponse)
async def get_detailed_reviews(
    airline_code: str,
    # 필터 파라미터
    departure_airport: Optional[str] = Query(None, description="출발 공항 코드 (예: ICN)"),
    arrival_airport: Optional[str] = Query(None, description="도착 공항 코드 (예: CDG)"),
    seat_class: Optional[str] = Query(None, description="좌석 등급: 전체, 프리미엄 이코노미, 이코노미, 비즈니스, 퍼스트"),
    period: Optional[str] = Query(None, description="기간: 전체, 최근 3개월, 최근 6개월, 최근 1년"),
    min_rating: Optional[int] = Query(None, ge=1, le=5, description="최소 평점 (1~5)"),
    photo_only: Optional[bool] = Query(False, description="사진/동영상 리뷰만 보기"),
    # 정렬 및 페이지네이션
    sort: str = Query("latest", description="정렬 옵션: latest, recommended, rating_high, rating_low, likes_high"),
    limit: int = Query(20, ge=1, le=100, description="조회할 리뷰 개수"),
    offset: int = Query(0, ge=0, description="오프셋"),
    service: ReviewsService = Depends(get_reviews_service)
):
    """
    항공사 상세 리뷰 페이지 정보를 조회합니다 (필터링 및 정렬 지원).
    
    ### 필터 옵션
    - **departure_airport**: 출발 공항 코드 (예: ICN)
    - **arrival_airport**: 도착 공항 코드 (예: CDG)
    - **seat_class**: 좌석 등급 (전체, 프리미엄 이코노미, 이코노미, 비즈니스, 퍼스트)
    - **period**: 기간 (전체, 최근 3개월, 최근 6개월, 최근 1년)
    - **min_rating**: 최소 평점 (1~5)
    - **photo_only**: 사진/동영상 리뷰만 보기 (true/false)
    
    ### 정렬 옵션
    - **latest**: 최신순 (기본값)
    - **recommended**: 추천순 (좋아요 많은 순)
    - **rating_high**: 평점 높은 순
    - **rating_low**: 평점 낮은 순
    - **likes_high**: 좋아요 많은 순 (recommended와 동일)
    
    ### 페이지네이션
    - **limit**: 조회할 리뷰 개수 (기본값: 20, 최대: 100)
    - **offset**: 오프셋 (기본값: 0)
    
    응답에는 전체 평점, 카테고리별 평점, 사진 리뷰 갤러리, 필터링 및 정렬된 개별 리뷰 목록이 포함됩니다.
    """
    try:
        filter_request = reviews_schemas.ReviewFilterRequest(
            departure_airport=departure_airport,
            arrival_airport=arrival_airport,
            seat_class=seat_class,
            period=period,
            min_rating=min_rating,
            photo_only=photo_only
        )
        
        return await service.get_detailed_reviews_page(
            airline_code=airline_code,
            filter_request=filter_request,
            sort=sort,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/filtered/{airline_code}", response_model=reviews_schemas.FilteredReviewsResponse)
async def get_filtered_reviews(
    airline_code: str,
    filter_request: reviews_schemas.ReviewFilterRequest,
    sort: str = Query("latest", description="정렬 옵션: latest, recommended, rating_high, rating_low, likes_high"),
    limit: int = Query(20, ge=1, le=100, description="조회할 리뷰 개수"),
    offset: int = Query(0, ge=0, description="오프셋"),
    service: ReviewsService = Depends(get_reviews_service)
):
    """
    필터링 및 정렬된 리뷰를 조회합니다 (POST 방식).
    
    필터 조건을 Request Body로 전달할 수 있습니다.
    """
    try:
        return await service.get_filtered_reviews(
            airline_code=airline_code,
            filter_request=filter_request,
            sort=sort,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
