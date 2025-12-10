"""
리뷰 관련 비즈니스 로직
"""

import json
from typing import List, Optional, Tuple
from datetime import datetime, timedelta, timezone
from fastapi.concurrency import run_in_threadpool

from app.core.firebase import db
from app.feature.reviews.reviews_schemas import (
    ReviewSchema,
    ReviewFilterRequest,
    FilteredReviewsResponse,
    DetailedReviewsResponse,
    BIMOSummaryResponse,
)
from app.feature.llm import llm_service
from app.core.exceptions.exceptions import (
    DatabaseError,
    ReviewNotFoundError,
    CustomException,
)

# Firestore 컬렉션 참조
reviews_collection = db.collection("reviews")
airlines_collection = db.collection("airlines")


async def get_reviews_by_airline(airline_code: str, limit: int = 10) -> List[ReviewSchema]:
    """
    항공사 코드로 리뷰를 조회합니다.
    
    Args:
        airline_code: 항공사 코드 (예: "KE", "OZ")
        limit: 조회할 리뷰 개수 (기본값: 10)
        
    Returns:
        리뷰 목록
    """
    try:
        query = reviews_collection.where("airlineCode", "==", airline_code).limit(limit)
        docs = await run_in_threadpool(lambda: list(query.stream()))
        
        reviews = []
        for doc in docs:
            review_data = doc.to_dict()
            review_data["id"] = doc.id
            reviews.append(ReviewSchema(**review_data))
        
        return reviews
    except Exception as e:
        if isinstance(e, CustomException):
            raise e
        raise DatabaseError(message=f"리뷰 조회 중 오류 발생: {e}")


async def get_review_by_id(review_id: str) -> ReviewSchema:
    """
    리뷰 ID로 리뷰를 조회합니다.
    
    Args:
        review_id: 리뷰 ID
        
    Returns:
        리뷰 정보
        
    Raises:
        ReviewNotFoundError: 리뷰를 찾을 수 없을 때
    """
    try:
        doc_ref = reviews_collection.document(review_id)
        doc = await run_in_threadpool(doc_ref.get)
        
        if not doc.exists:
            raise ReviewNotFoundError(review_id=review_id)
        
        review_data = doc.to_dict()
        return ReviewSchema(**review_data)
    except ReviewNotFoundError:
        raise
    except Exception as e:
        if isinstance(e, CustomException):
            raise e
        raise DatabaseError(message=f"리뷰 조회 중 오류 발생: {e}")


async def summarize_reviews(
    airline_code: str,
    airline_name: Optional[str] = None,
    limit: int = 20
) -> str:
    """
    LLM을 사용하여 항공사 리뷰를 요약합니다.
    
    Args:
        airline_code: 항공사 코드
        airline_name: 항공사 이름 (선택사항)
        limit: 요약에 사용할 리뷰 개수 (기본값: 20)
        
    Returns:
        요약된 리뷰 텍스트
    """
    # 1. 리뷰 조회
    reviews = await get_reviews_by_airline(airline_code, limit=limit)
    
    if not reviews:
        return f"{airline_name or airline_code} 항공사에 대한 리뷰가 아직 없습니다."
    
    # 2. 리뷰 텍스트 수집
    review_texts = []
    ratings_summary = {
        "seatComfort": [],
        "inflightMeal": [],
        "service": [],
        "cleanliness": [],
        "checkIn": []
    }
    
    for review in reviews:
        if review.text:
            review_texts.append(f"- {review.text} (평점: {review.overallRating}/5)")
        
        # 평점 수집
        if review.ratings:
            ratings_summary["seatComfort"].append(review.ratings.seatComfort)
            ratings_summary["inflightMeal"].append(review.ratings.inflightMeal)
            ratings_summary["service"].append(review.ratings.service)
            ratings_summary["cleanliness"].append(review.ratings.cleanliness)
            ratings_summary["checkIn"].append(review.ratings.checkIn)
    
    # 3. 평균 평점 계산
    avg_ratings = {}
    for key, values in ratings_summary.items():
        if values:
            avg_ratings[key] = sum(values) / len(values)
    
    # 4. LLM 프롬프트 구성
    airline_display = airline_name or airline_code
    prompt = f"""다음은 {airline_display} 항공사에 대한 {len(reviews)}개의 리뷰입니다.

평균 평점:
- 좌석 편안함: {avg_ratings.get('seatComfort', 0):.1f}/5
- 기내식: {avg_ratings.get('inflightMeal', 0):.1f}/5
- 서비스: {avg_ratings.get('service', 0):.1f}/5
- 청결도: {avg_ratings.get('cleanliness', 0):.1f}/5
- 체크인: {avg_ratings.get('checkIn', 0):.1f}/5

리뷰 내용:
{chr(10).join(review_texts[:50])}  # 최대 50개만 전달

위 리뷰들을 종합적으로 분석하여 다음 형식으로 요약해주세요:

1. 전체적인 평가 (2-3문장)
2. 주요 장점 (3-5개 항목)
3. 주요 단점 또는 개선점 (3-5개 항목)
4. 추천 대상 (누가 이 항공사를 선택하면 좋을지)

요약은 객관적이고 균형잡힌 시각으로 작성해주세요."""

    # 5. LLM 호출
    system_instruction = (
        "You are an airline review analyst. "
        "Analyze and summarize airline reviews objectively and comprehensively. "
        "Provide balanced insights highlighting both strengths and areas for improvement."
    )
    
    from app.feature.llm.llm_schemas import LLMChatRequest
    request = LLMChatRequest(
        prompt=prompt,
        system_instruction=system_instruction
    )
    
    summary = await llm_service.generate_chat_completion(request)
    return summary


async def get_airline_reviews_summary(
    airline_code: str,
    airline_name: Optional[str] = None
) -> dict:
    """
    항공사 리뷰 요약을 가져옵니다.
    
    Args:
        airline_code: 항공사 코드
        airline_name: 항공사 이름 (선택사항)
        
    Returns:
        {
            "airline_code": str,
            "airline_name": str,
            "summary": str,
            "review_count": int
        }
    """
    reviews = await get_reviews_by_airline(airline_code, limit=100)
    
    if not reviews:
        return {
            "airline_code": airline_code,
            "airline_name": airline_name or airline_code,
            "summary": f"{airline_name or airline_code} 항공사에 대한 리뷰가 아직 없습니다.",
            "review_count": 0
        }
    
    summary = await summarize_reviews(airline_code, airline_name, limit=50)
    
    return {
        "airline_code": airline_code,
        "airline_name": airline_name or airline_code,
        "summary": summary,
        "review_count": len(reviews)
    }


def _parse_route(route: str) -> Tuple[Optional[str], Optional[str]]:
    """
    노선 문자열을 파싱하여 출발지와 도착지를 반환합니다.
    
    Args:
        route: 노선 문자열 (예: "ICN-CDG", "인천-파리")
        
    Returns:
        (출발지 코드, 도착지 코드) 튜플
    """
    if not route:
        return None, None
    
    # "-" 또는 " - "로 분리
    parts = route.replace(" ", "").split("-")
    if len(parts) >= 2:
        return parts[0].upper(), parts[1].upper()
    return None, None


def _matches_route_filter(review: ReviewSchema, departure: Optional[str], arrival: Optional[str]) -> bool:
    """리뷰가 노선 필터 조건에 맞는지 확인"""
    if not departure and not arrival:
        return True
    
    review_dep, review_arr = _parse_route(review.route)
    
    if departure and review_dep != departure.upper():
        return False
    if arrival and review_arr != arrival.upper():
        return False
    
    return True


def _matches_seat_class_filter(review: ReviewSchema, seat_class: Optional[str]) -> bool:
    """리뷰가 좌석 등급 필터 조건에 맞는지 확인"""
    if not seat_class or seat_class == "전체":
        return True
    
    if not review.seatClass:
        return False
    
    # 좌석 등급 매칭 (대소문자 무시)
    return review.seatClass.lower() == seat_class.lower()


async def generate_bimo_summary(airline_code: str) -> BIMOSummaryResponse:
    """
    LLM을 사용해 Good/Bad 포인트를 JSON 형태로 추출합니다.
    실패 시 빈 리스트를 반환하여 프런트가 우회 표시 가능.
    """
    # 최근 리뷰 최대 50개 사용
    reviews = await get_reviews_by_airline(airline_code, limit=50)
    if not reviews:
        return BIMOSummaryResponse(
            airline_code=airline_code,
            airline_name=airline_code,
            good_points=[],
            bad_points=[],
            review_count=0,
        )

    airline_name = reviews[0].airlineName if getattr(reviews[0], "airlineName", None) else airline_code

    review_lines = []
    for r in reviews:
        text = r.text or ""
        review_lines.append(f"- {text} (평점: {r.overallRating}/5)")

    prompt = f"""
다음은 {airline_name} 항공사에 대한 리뷰 {len(reviews)}개의 목록입니다.
각 리뷰는 텍스트와 평점을 포함합니다.

리뷰 목록:
{chr(10).join(review_lines[:50])}

요구사항:
- 한국어로 응답합니다.
- JSON 문자열만 반환합니다 (설명 금지).
- 형태: {{"good_points": ["..."], "bad_points": ["..."]}}
- good/bad 각각 최대 5개, 짧고 핵심만.
"""

    system_instruction = (
        "You are an airline review analyst. Return concise JSON with good_points and bad_points in Korean."
    )

    from app.feature.llm.llm_schemas import LLMChatRequest
    request = LLMChatRequest(prompt=prompt, system_instruction=system_instruction)

    raw = await llm_service.generate_chat_completion(request)

    def _safe_parse(raw_text: str) -> tuple[list[str], list[str]]:
        try:
            data = json.loads(raw_text.strip())
            good = data.get("good_points") or []
            bad = data.get("bad_points") or []
            return list(good), list(bad)
        except Exception:
            # 간단한 fallback: 줄바꿈 기준으로 good/bad 추정하지 않고 빈 리스트로 처리
            return [], []

    good_points, bad_points = _safe_parse(raw)

    return BIMOSummaryResponse(
        airline_code=airline_code,
        airline_name=airline_name,
        good_points=good_points,
        bad_points=bad_points,
        review_count=len(reviews),
    )


def _matches_period_filter(review: ReviewSchema, period: Optional[str]) -> bool:
    """리뷰가 기간 필터 조건에 맞는지 확인"""
    if not period or period == "전체":
        return True
    
    now = datetime.now(timezone.utc)
    review_date = review.createdAt
    
    if isinstance(review_date, str):
        try:
            review_date = datetime.fromisoformat(review_date.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return True  # 파싱 실패 시 포함
    
    delta_map = {
        "최근 3개월": timedelta(days=90),
        "최근 6개월": timedelta(days=180),
        "최근 1년": timedelta(days=365),
    }
    
    delta = delta_map.get(period)
    if not delta:
        return True
    
    return (now - review_date) <= delta


def _matches_rating_filter(review: ReviewSchema, min_rating: Optional[int]) -> bool:
    """리뷰가 평점 필터 조건에 맞는지 확인"""
    if min_rating is None:
        return True
    
    return review.overallRating >= min_rating


def _matches_photo_filter(review: ReviewSchema, photo_only: bool) -> bool:
    """리뷰가 사진 필터 조건에 맞는지 확인"""
    if not photo_only:
        return True
    
    return review.imageUrl is not None and review.imageUrl != ""


async def get_filtered_reviews(
    airline_code: str,
    filter_request: ReviewFilterRequest,
    sort: str = "latest",
    limit: int = 20,
    offset: int = 0
) -> FilteredReviewsResponse:
    """
    필터링 및 정렬된 리뷰를 조회합니다.
    
    Args:
        airline_code: 항공사 코드
        filter_request: 필터 조건
        sort: 정렬 옵션 ("latest", "recommended", "rating_high", "rating_low", "likes_high")
        limit: 조회할 리뷰 개수
        offset: 오프셋
        
    Returns:
        FilteredReviewsResponse
    """
    try:
        # 1. 항공사 정보 조회
        airline_doc = await run_in_threadpool(
            lambda: airlines_collection.document(airline_code).get()
        )
        
        if not airline_doc.exists:
            raise DatabaseError(message=f"항공사를 찾을 수 없습니다: {airline_code}")
        
        airline_data = airline_doc.to_dict()
        airline_name = airline_data.get("airlineName", airline_code)
        
        # 2. 모든 리뷰 조회
        query = reviews_collection.where("airlineCode", "==", airline_code)
        docs = await run_in_threadpool(lambda: list(query.stream()))
        
        # 3. ReviewSchema로 변환
        all_reviews = []
        for doc in docs:
            try:
                data = doc.to_dict()
                data["id"] = doc.id
                review = ReviewSchema(**data)
                all_reviews.append(review)
            except (ValueError, TypeError, KeyError) as e:
                continue  # 스키마 변환 실패 시 스킵
        
        # 4. 필터링 적용
        filtered_reviews = []
        for review in all_reviews:
            if not _matches_route_filter(review, filter_request.departure_airport, filter_request.arrival_airport):
                continue
            if not _matches_seat_class_filter(review, filter_request.seat_class):
                continue
            if not _matches_period_filter(review, filter_request.period):
                continue
            if not _matches_rating_filter(review, filter_request.min_rating):
                continue
            if not _matches_photo_filter(review, filter_request.photo_only):
                continue
            
            filtered_reviews.append(review)
        
        # 5. 정렬 적용
        if sort == "latest":
            filtered_reviews.sort(key=lambda x: x.createdAt, reverse=True)
        elif sort == "recommended" or sort == "likes_high":
            filtered_reviews.sort(key=lambda x: x.likes, reverse=True)
        elif sort == "rating_high":
            filtered_reviews.sort(key=lambda x: x.overallRating, reverse=True)
        elif sort == "rating_low":
            filtered_reviews.sort(key=lambda x: x.overallRating)
        
        # 6. 페이지네이션 적용
        total_count = len(filtered_reviews)
        paginated_reviews = filtered_reviews[offset:offset + limit]
        has_more = offset + limit < total_count
        
        return FilteredReviewsResponse(
            airline_code=airline_code,
            airline_name=airline_name,
            total_count=total_count,
            reviews=paginated_reviews,
            has_more=has_more
        )
    except Exception as e:
        if isinstance(e, CustomException):
            raise e
        raise DatabaseError(message=f"필터링된 리뷰 조회 중 오류 발생: {e}")


async def get_detailed_reviews_page(
    airline_code: str,
    filter_request: Optional[ReviewFilterRequest] = None,
    sort: str = "latest",
    limit: int = 20,
    offset: int = 0
) -> DetailedReviewsResponse:
    """
    항공사 상세 리뷰 페이지 정보를 조회합니다 (필터링 및 정렬 지원).
    
    Args:
        airline_code: 항공사 코드
        filter_request: 필터 조건 (선택적)
        sort: 정렬 옵션 ("latest", "recommended", "rating_high", "rating_low", "likes_high")
        limit: 조회할 리뷰 개수
        offset: 오프셋
        
    Returns:
        DetailedReviewsResponse (사진 갤러리 포함)
    """
    try:
        # 필터가 없으면 기본 필터 사용
        if filter_request is None:
            filter_request = ReviewFilterRequest()
        
        # 필터링된 리뷰 조회
        filtered_response = await get_filtered_reviews(
            airline_code=airline_code,
            filter_request=filter_request,
            sort=sort,
            limit=limit,
            offset=offset
        )
        
        # 항공사 정보 및 평점 조회
        airline_doc = await run_in_threadpool(
            lambda: airlines_collection.document(airline_code).get()
        )
        
        if not airline_doc.exists:
            raise DatabaseError(message=f"항공사를 찾을 수 없습니다: {airline_code}")
        
        airline_data = airline_doc.to_dict()
        airline_name = airline_data.get("airlineName", airline_code)
        
        # 평점 정보
        avg_ratings = airline_data.get("averageRatings", {})
        overall_rating = airline_data.get("overallRating", 0.0)
        if not overall_rating and avg_ratings:
            overall_rating = round(sum(avg_ratings.values()) / len(avg_ratings), 2)
        
        # 사진 리뷰 수집
        photo_urls = []
        for review in filtered_response.reviews:
            if review.imageUrl:
                photo_urls.append(review.imageUrl)
        
        return DetailedReviewsResponse(
            airline_code=airline_code,
            airline_name=airline_name,
            overall_rating=overall_rating,
            total_reviews=filtered_response.total_count,
            average_ratings=avg_ratings,
            photo_reviews=photo_urls,
            photo_count=len(photo_urls),
            reviews=filtered_response.reviews,
            has_more=filtered_response.has_more
        )
    except Exception as e:
        if isinstance(e, CustomException):
            raise e
        raise DatabaseError(message=f"상세 리뷰 페이지 조회 중 오류 발생: {e}")


