"""
항공사 관련 비즈니스 로직
경로: airlines/{airlineCode}
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from fastapi.concurrency import run_in_threadpool

from app.core.firebase import db
from app.feature.airlines.models import Airline, AirlineDetail
from app.feature.flights.flights_schemas import AirlineSchema
from app.core.exceptions.exceptions import DatabaseError, CustomException

# Firestore 컬렉션 참조
airlines_collection = db.collection("airlines")
reviews_collection = db.collection("reviews")


async def search_airlines(query: str) -> List[Airline]:
    """
    항공사 이름으로 검색 (Firestore는 full-text search가 약하므로
    실제론 Algolia 등을 쓰거나, 여기선 단순 startswith/equality 데모)
    """
    # 실제 구현: 부분 일치 검색을 위해선 별도 인덱싱 필요.
    # 여기서는 단순 쿼리 예시
    if not query:
        return []
        
    try:
        # 데모 로직: 전체 다 가져와서 필터링 (데이터가 적다는 가정)
        # 프로덕션에서는 절대 이렇게 하면 안됨.
        docs = await run_in_threadpool(lambda: list(airlines_collection.stream()))
        results = []
        query_lower = query.lower()
        
        for doc in docs:
            data = doc.to_dict()
            airline_name = data.get("airlineName", "")
            
            # AirlineSchema를 Airline 모델로 변환
            if query_lower in airline_name.lower():
                airline = Airline(
                    id=doc.id,
                    name=airline_name,
                    code=doc.id,
                    country=data.get("country", ""),
                    alliance=data.get("alliance"),
                    type=data.get("type", "FSC"),
                    rating=data.get("averageRatings", {}).get("overall", 0.0),
                    review_count=data.get("totalReviews", 0),
                    logo_url=data.get("logoUrl"),
                )
                results.append(airline)
        
        return results
    except Exception as e:
        if isinstance(e, CustomException):
            raise e
        raise DatabaseError(message=f"항공사 검색 중 오류 발생: {e}")


async def get_popular_airlines(limit: int = 5) -> List[Airline]:
    """
    인기 항공사 조회 (Weighted Rating 기준)
    
    IMDB 공식 사용:
    WR = (v / (v+m)) * R + (m / (v+m)) * C
    - v: 해당 항공사의 총 리뷰 수
    - m: 순위에 들기 위한 최소 리뷰 수 (여기서는 10으로 설정)
    - R: 해당 항공사의 평균 평점
    - C: 전체 리포트의 평균 평점
    """
    try:
        # 모든 항공사 조회 (통계 계산을 위해)
        docs = await run_in_threadpool(lambda: list(airlines_collection.stream()))
        
        all_airlines = []
        total_rating_sum = 0
        count_for_mean = 0
        
        # 1. 데이터 수집 및 평균 계산 준비
        for doc in docs:
            data = doc.to_dict()
            rating = data.get("averageRatings", {}).get("overall", 0.0)
            review_count = data.get("totalReviews", 0)
            
            # AirlineSchema를 Airline 모델로 변환
            airline = Airline(
                id=doc.id,
                name=data.get("airlineName", ""),
                code=doc.id,
                country=data.get("country", ""),
                alliance=data.get("alliance"),
                type=data.get("type", "FSC"),
                rating=rating,
                review_count=review_count,
                logo_url=data.get("logoUrl"),
            )
            
            all_airlines.append(airline)
            
            # 0점인 경우 평균 계산에서 제외할 수도 있으나, 여기선 포함
            if review_count > 0:
                total_rating_sum += rating
                count_for_mean += 1
                
        # 2. 전체 평균(C) 계산
        C = total_rating_sum / count_for_mean if count_for_mean > 0 else 0
        m = 10  # 최소 리뷰 수 기준 (조정 가능)
        
        # 3. 가중 평점 계산 및 정렬
        # (v / (v+m)) * R + (m / (v+m)) * C
        def weighted_rating(airline: Airline, C: float, m: int) -> float:
            v = airline.review_count
            R = airline.rating
            if v == 0:
                return 0
            return (v / (v + m)) * R + (m / (v + m)) * C

        # 가중 평점 계산 후 정렬
        sorted_airlines = sorted(
            all_airlines, 
            key=lambda a: weighted_rating(a, C, m), 
            reverse=True
        )
        
        # 4. 순위 할당 및 상위 항목 반환
        result = []
        for index, airline in enumerate(sorted_airlines[:limit]):
            airline.rank = index + 1
            result.append(airline)
            
        return result
            
    except Exception as e:
        if isinstance(e, CustomException):
            raise e
        raise DatabaseError(message=f"인기 항공사 조회 중 오류 발생: {e}")


def _get_week_date_range(year: int, month: int, week: int) -> tuple[datetime, datetime]:
    """
    특정 연/월의 주차(start, end)를 UTC 기준으로 계산합니다.
    주차는 1주차를 그 달의 1일~7일, 2주차를 8~14일 식으로 단순 분할합니다.
    """
    if week < 1:
        raise ValueError("week는 1 이상이어야 합니다.")
    start = datetime(year, month, 1, tzinfo=timezone.utc) + timedelta(days=(week - 1) * 7)
    end = start + timedelta(days=7)
    return start, end


async def get_popular_airlines_weekly(year: int, month: int, week: int, limit: int = 5) -> List[Airline]:
    """
    특정 연/월/주차 기준 인기 항공사 조회 (리뷰/평점 기반 가중 점수)
    - 주차는 단순히 7일 단위로 끊어서 계산 (1주차: 1~7일, 2주차: 8~14일 ...)
    """
    try:
        start_date, end_date = _get_week_date_range(year, month, week)

        # 1) 해당 기간 리뷰 조회
        query = (
            reviews_collection.where("createdAt", ">=", start_date)
            .where("createdAt", "<", end_date)
        )
        review_docs = await run_in_threadpool(lambda: list(query.stream()))

        # 2) 항공사별 리뷰 합계/평균 집계
        aggregates: Dict[str, Dict[str, float]] = {}
        for doc in review_docs:
            data = doc.to_dict()
            code = data.get("airlineCode")
            rating = data.get("overallRating", 0.0)
            if not code:
                continue
            bucket = aggregates.setdefault(code, {"sum": 0.0, "count": 0})
            bucket["sum"] += rating
            bucket["count"] += 1

        if not aggregates:
            return []

        # 3) 항공사 메타데이터 조회 (이름/로고 등)
        def _fetch_airline_docs(codes: List[str]):
            result = {}
            for c in codes:
                result[c] = airlines_collection.document(c).get()
            return result

        codes = list(aggregates.keys())
        airline_docs = await run_in_threadpool(lambda: _fetch_airline_docs(codes))

        # 전체 평균 C 계산
        total_rating_sum = sum(v["sum"] for v in aggregates.values())
        total_count = sum(v["count"] for v in aggregates.values())
        C = total_rating_sum / total_count if total_count > 0 else 0
        m = 10

        # 4) Airline 모델 변환
        all_airlines: List[Airline] = []
        for code, agg in aggregates.items():
            doc = airline_docs.get(code)
            data = doc.to_dict() if doc and doc.exists else {}
            avg_rating = agg["sum"] / agg["count"] if agg["count"] > 0 else 0.0
            airline = Airline(
                id=code,
                name=data.get("airlineName", code),
                code=code,
                country=data.get("country", ""),
                alliance=data.get("alliance"),
                type=data.get("type", "FSC"),
                rating=round(avg_rating, 2),
                review_count=int(agg["count"]),
                logo_url=data.get("logoUrl"),
            )
            all_airlines.append(airline)

        # 5) 가중 평점 정렬
        def weighted_rating(airline: Airline, C: float, m: int) -> float:
            v = airline.review_count
            R = airline.rating
            if v == 0:
                return 0
            return (v / (v + m)) * R + (m / (v + m)) * C

        sorted_airlines = sorted(
            all_airlines,
            key=lambda a: weighted_rating(a, C, m),
            reverse=True,
        )

        # 6) 순위 부여
        result = []
        for idx, airline in enumerate(sorted_airlines[:limit]):
            airline.rank = idx + 1
            result.append(airline)

        return result

    except Exception as e:
        if isinstance(e, CustomException):
            raise e
        raise DatabaseError(message=f\"주차별 인기 항공사 조회 중 오류 발생: {e}\")


async def get_airline_detail(airline_code: str) -> Optional[AirlineDetail]:
    """항공사 상세 정보 조회 (레거시, AirlineDetail 모델 사용)"""
    try:
        doc_ref = airlines_collection.document(airline_code)
        doc = await run_in_threadpool(doc_ref.get)
        
        if not doc.exists:
            return None
        
        data = doc.to_dict()
        
        # 전체 평균 평점 계산 (카테고리별 평균의 평균)
        avg_ratings = data.get("averageRatings", {})
        if avg_ratings:
            overall_rating = sum(avg_ratings.values()) / len(avg_ratings)
        else:
            overall_rating = 0.0
        
        # AirlineSchema 데이터를 AirlineDetail 모델로 변환
        airline_detail = AirlineDetail(
            id=airline_code,
            name=data.get("airlineName", ""),
            name_en=data.get("airlineNameEn"),
            code=airline_code,
            country=data.get("country", ""),
            alliance=data.get("alliance"),
            type=data.get("type", "FSC"),
            rating=overall_rating,
            review_count=data.get("totalReviews", 0),
            logo_url=data.get("logoUrl"),
            description=data.get("description"),
            hub_airport=data.get("hubAirport"),
            hub_airport_name=data.get("hubAirportName"),
            operating_classes=data.get("operatingClasses", []),
            images=data.get("images", []),
            total_reviews=data.get("totalReviews", 0),
            average_ratings=avg_ratings,
            rating_breakdown=data.get("ratingBreakdown", {}),
            overall_rating=overall_rating,
        )
        
        return airline_detail
    except Exception as e:
        if isinstance(e, CustomException):
            raise e
        raise DatabaseError(message=f"항공사 상세 정보 조회 중 오류 발생: {e}")


async def get_airline_statistics(airline_code: str) -> Optional[AirlineSchema]:
    """
    항공사의 집계된 통계 정보를 조회합니다.
    Cloud Function에 의해 자동 업데이트되는 데이터입니다.
    화면에 표시되는 모든 정보를 포함합니다.
    
    Args:
        airline_code: 항공사 코드
        
    Returns:
        AirlineSchema (없으면 None)
    """
    try:
        doc_ref = airlines_collection.document(airline_code)
        doc = await run_in_threadpool(doc_ref.get)
        
        if not doc.exists:
            return None
        
        data = doc.to_dict()
        
        # 전체 평균 평점 계산 (카테고리별 평균의 평균)
        avg_ratings = data.get("averageRatings", {})
        if avg_ratings:
            overall_rating = round(sum(avg_ratings.values()) / len(avg_ratings), 2)
        else:
            overall_rating = 0.0
        
        # overallRating 필드 추가
        data["overallRating"] = overall_rating
        
        return AirlineSchema(**data)
    except Exception as e:
        if isinstance(e, CustomException):
            raise e
        raise DatabaseError(message=f"항공사 통계 조회 중 오류 발생: {e}")

