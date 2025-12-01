"""
리뷰 관련 비즈니스 로직
"""

from typing import List, Optional
from fastapi.concurrency import run_in_threadpool

from app.core.firebase import db
from app.feature.reviews.reviews_schemas import ReviewSchema
from app.feature.LLM import llm_service
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
    
    from app.feature.LLM.llm_schemas import LLMChatRequest
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


