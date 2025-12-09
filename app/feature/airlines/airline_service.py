"""
항공사 관련 비즈니스 로직
경로: airlines/{airlineCode}
"""

from typing import List, Optional
from fastapi.concurrency import run_in_threadpool

from app.core.firebase import db
from app.feature.airlines.models import Airline, AirlineDetail
from app.feature.flights.flights_schemas import AirlineSchema
from app.core.exceptions.exceptions import DatabaseError, CustomException

# Firestore 컬렉션 참조
airlines_collection = db.collection("airlines")


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
    """인기 항공사 조회 (평점 높은 순)"""
    try:
        # AirlineSchema 기반으로 조회 (totalReviews가 많은 순)
        query = airlines_collection.order_by(
            "totalReviews", direction="DESCENDING"
        ).limit(limit)
        
        docs = await run_in_threadpool(lambda: list(query.stream()))
        
        results = []
        for doc in docs:
            data = doc.to_dict()
            # AirlineSchema를 Airline 모델로 변환
            airline = Airline(
                id=doc.id,
                name=data.get("airlineName", ""),
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
        raise DatabaseError(message=f"항공사 조회 중 오류 발생: {e}")


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

