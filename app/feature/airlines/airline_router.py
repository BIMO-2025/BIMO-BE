"""
항공사 관련 API 라우터
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.deps import get_firebase_service
from app.core.firebase import FirebaseService
from app.feature.airlines.airline_service import AirlineService
from app.feature.airlines.models import Airline, AirlineDetail
from app.feature.flights.flights_schemas import AirlineSchema
from app.feature.reviews.reviews_schemas import AirlineReviewsResponse, BIMOSummaryResponse
from app.feature.reviews.reviews_router import get_reviews_service
from app.feature.reviews.reviews_service import ReviewsService

router = APIRouter(
    prefix="/airlines",
    tags=["Airlines"],
    responses={404: {"description": "Not found"}},
)


def get_airline_service(
    firebase_service: FirebaseService = Depends(get_firebase_service)
) -> AirlineService:
    """AirlineService 의존성 주입"""
    return AirlineService(firebase_service=firebase_service)


@router.get("/search", response_model=List[Airline])
async def search_airlines(
    query: str,
    service = Depends(get_airline_service)
):
    """
    항공사 이름으로 검색합니다.
    
    - **query**: 검색어 (항공사 이름)
    """
    return await service.search_airlines(query)


@router.get("/sorting", response_model=List[Airline])
async def get_airlines_sorted_by_rating(
    service = Depends(get_airline_service)
):
    """
    모든 항공사를 overallRating 순으로 정렬하여 조회합니다.
    
    Firestore airlines collection에 저장된 항공사들을 overallRating 내림차순으로 정렬하여 반환합니다.
    """
    return await service.get_airlines_sorted_by_rating()


@router.get("/{airline_code}", response_model=AirlineSchema)
async def get_airline_detail(
    airline_code: str,
    service = Depends(get_airline_service)
):
    """
    항공사 상세 정보를 조회합니다.
    
    화면에 표시되는 모든 정보를 포함합니다:
    - 기본 정보 (이름, 로고, 이미지)
    - 평점 정보 (전체 평균, 카테고리별 평균)
    - 집계 통계 (리뷰 수, 점수 분포)
    - 기본 정보 (본사 위치, 허브 공항, 항공 동맹, 운항 클래스)
    
    - **airline_code**: 항공사 코드 (예: KE, AF, SQ)
    """
    airline = await service.get_airline_statistics(airline_code)
    if not airline:
        raise HTTPException(status_code=404, detail="항공사를 찾을 수 없습니다.")
    return airline


@router.get("/{airline_code}/statistics", response_model=AirlineSchema)
async def get_airline_statistics(
    airline_code: str,
    service = Depends(get_airline_service)
):
    """
    항공사의 집계된 통계 정보만 조회합니다.
    Cloud Function에 의해 자동 업데이트되는 데이터입니다.
    
    - **airline_code**: 항공사 코드
    """
    stats = await service.get_airline_statistics(airline_code)
    if not stats:
        raise HTTPException(status_code=404, detail="항공사를 찾을 수 없습니다.")
    return stats


@router.get("/{airline_code}/reviews", response_model=AirlineReviewsResponse)
async def get_airline_reviews_page(
    airline_code: str,
    sort: str = Query("latest", description="정렬 옵션: latest, recommended, rating_high, rating_low"),
    limit: int = Query(20, ge=1, le=100, description="조회할 리뷰 개수"),
    offset: int = Query(0, ge=0, description="오프셋"),
    reviews_service: ReviewsService = Depends(get_reviews_service)
):
    """
    항공사 리뷰 페이지 정보를 조회합니다.
    
    - **airline_code**: 항공사 코드
    - **sort**: 정렬 옵션 (latest, recommended, rating_high, rating_low)
    - **limit**: 조회할 리뷰 개수 (기본값: 20, 최대: 100)
    - **offset**: 오프셋 (기본값: 0)
    
    평점 정보와 리뷰 목록을 반환합니다.
    """
    return await reviews_service.get_airline_reviews_page(
        airline_code=airline_code,
        sort=sort,
        limit=limit,
        offset=offset
    )


@router.get("/{airline_code}/summary", response_model=BIMOSummaryResponse)
async def get_bimo_summary(
    airline_code: str,
    reviews_service: ReviewsService = Depends(get_reviews_service)
):
    """
    BIMO 요약 정보를 조회합니다 (LLM 기반).
    Good/Bad 포인트를 분리하여 반환합니다.
    
    - **airline_code**: 항공사 코드
    
    평점 관련 요청과 별도로 호출됩니다.
    """
    return await reviews_service.generate_bimo_summary(airline_code)

