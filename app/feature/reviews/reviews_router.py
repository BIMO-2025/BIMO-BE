"""
리뷰 관련 API 라우터
"""
from __future__ import annotations

from fastapi import APIRouter, Query, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Annotated

from app.core.deps import get_firebase_service, get_gemini_client
from app.core.firebase import FirebaseService
from app.core.security import verify_firebase_token
from app.feature.llm.gemini_client import GeminiClient
from app.feature.reviews.reviews_service import ReviewsService
from app.feature.reviews import reviews_schemas

router = APIRouter(
    prefix="/reviews",
    tags=["Reviews"],
    responses={404: {"description": "Not found"}},
)

security = HTTPBearer()


def get_reviews_service(
    firebase_service = Depends(get_firebase_service),
    gemini_client = Depends(get_gemini_client)
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


@router.post("", response_model=reviews_schemas.ReviewSchema, status_code=201)
async def create_review(
    review: reviews_schemas.ReviewSchema,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    service: ReviewsService = Depends(get_reviews_service)
):
    """
    새로운 리뷰를 생성합니다.
    
    - **인증 필요**: Bearer Token
    - 리뷰 작성 시 항공사 통계가 자동으로 업데이트됩니다
    
    Request Body:
    - userId: 사용자 ID
    - userNickname: 사용자 닉네임
    - airlineCode: 항공사 코드
    - airlineName: 항공사 이름
    - route: 노선 (예: "ICN-CDG")
    - flightNumber: 항공편 번호 (선택사항)
    - seatClass: 좌석 등급 (선택사항)
    - imageUrl: 사진 URL (선택사항)
    - ratings: 카테고리별 평점
      - seatComfort: 좌석 편안함
      - inflightMeal: 기내식
      - service: 서비스
      - cleanliness: 청결도
      - checkIn: 체크인
    - overallRating: 전체 평점 (1~5)
    - text: 리뷰 내용
    - isVerified: 인증 여부 (기본값: false)
    - likes: 좋아요 수 (기본값: 0)
    """
    try:
        # 토큰 검증
        token = credentials.credentials
        decoded_token = verify_firebase_token(token)
        user_id = decoded_token.get("uid")
        
        # 리뷰 생성
        created_review = await service.create_review(review, user_id)
        return created_review
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{review_id}", response_model=reviews_schemas.ReviewSchema)
async def update_review(
    review_id: str,
    review: reviews_schemas.ReviewSchema,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    service: ReviewsService = Depends(get_reviews_service)
):
    """
    기존 리뷰를 수정합니다.
    
    - **인증 필요**: Bearer Token (본인의 리뷰만 수정 가능)
    - 리뷰 수정 시 항공사 통계가 자동으로 업데이트됩니다
    - 항공사 코드 변경 시 이전 항공사와 새 항공사 모두 통계 업데이트
    
    Path Parameters:
    - review_id: 리뷰 ID
    
    Request Body는 create_review와 동일
    """
    try:
        # 토큰 검증
        token = credentials.credentials
        decoded_token = verify_firebase_token(token)
        user_id = decoded_token.get("uid")
        
        # 리뷰 수정
        updated_review = await service.update_review(review_id, review, user_id)
        return updated_review
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{review_id}")
async def delete_review(
    review_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    service: ReviewsService = Depends(get_reviews_service)
):
    """
    리뷰를 삭제합니다.
    
    - **인증 필요**: Bearer Token (본인의 리뷼만 삭제 가능)
    - 리뷰 삭제 시 항공사 통계가 자동으로 업데이트됩니다
    
    Path Parameters:
    - review_id: 리뷰 ID
    
    Returns:
    - message: 삭제 성공 메시지
    - review_id: 삭제된 리뷰 ID
    """
    try:
        # 토큰 검증
        token = credentials.credentials
        decoded_token = verify_firebase_token(token)
        user_id = decoded_token.get("uid")
        
        # 리뷰 삭제
        result = await service.delete_review(review_id, user_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
