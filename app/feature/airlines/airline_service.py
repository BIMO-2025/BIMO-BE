"""
항공사 관련 비즈니스 로직
경로: airlines/{airlineCode}
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from fastapi.concurrency import run_in_threadpool

from app.core.firebase import FirebaseService
from app.feature.airlines.models import Airline, AirlineDetail
from app.feature.flights.flights_schemas import AirlineSchema
from app.core.exceptions.exceptions import DatabaseError, CustomException


class AirlineService:
    """항공사 관련 비즈니스 로직을 처리하는 서비스 클래스"""
    
    def __init__(self, firebase_service: FirebaseService):
        """
        AirlineService 초기화
        
        Args:
            firebase_service: Firebase 서비스 인스턴스
        """
        self.db = firebase_service.db
        self.airlines_collection = self.db.collection("airlines")
        self.reviews_collection = self.db.collection("reviews")
    
    @staticmethod
    def _calculate_weighted_rating(airline: Airline, C: float, m: int) -> float:
        """
        IMDB 가중 평점 계산
        
        WR = (v / (v+m)) * R + (m / (v+m)) * C
        - v: 해당 항공사의 총 리뷰 수
        - m: 순위에 들기 위한 최소 리뷰 수
        - R: 해당 항공사의 평균 평점
        - C: 전체 평균 평점
        
        Args:
            airline: 항공사 모델
            C: 전체 평균 평점
            m: 최소 리뷰 수 기준
            
        Returns:
            가중 평점
        """
        v = airline.review_count
        R = airline.rating
        if v == 0:
            return 0
        return (v / (v + m)) * R + (m / (v + m)) * C
    
    async def search_airlines(self, query: str) -> List[Airline]:
        """
        항공사 이름으로 검색
        
        Args:
            query: 검색어
            
        Returns:
            검색된 항공사 목록
        """
        if not query:
            return []
            
        try:
            # 데모 로직: 전체 다 가져와서 필터링 (데이터가 적다는 가정)
            # 프로덕션에서는 Algolia 등 전문 검색 엔진 사용 권장
            docs = await run_in_threadpool(lambda: list(self.airlines_collection.stream()))
            results = []
            query_lower = query.lower()
            
            for doc in docs:
                data = doc.to_dict()
                airline_name = data.get("airlineName", "")
                
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
    
    async def get_popular_airlines(self, limit: int = 5) -> List[Airline]:
        """
        인기 항공사 조회 (Weighted Rating 기준)
        
        Args:
            limit: 반환할 최대 항공사 수
            
        Returns:
            인기 항공사 목록 (순위 포함)
        """
        try:
            # 모든 항공사 조회
            docs = await run_in_threadpool(lambda: list(self.airlines_collection.stream()))
            
            all_airlines = []
            total_rating_sum = 0
            count_for_mean = 0
            
            # 1. 데이터 수집 및 평균 계산 준비
            for doc in docs:
                data = doc.to_dict()
                rating = data.get("averageRatings", {}).get("overall", 0.0)
                review_count = data.get("totalReviews", 0)
                
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
                
                if review_count > 0:
                    total_rating_sum += rating
                    count_for_mean += 1
                    
            # 2. 전체 평균(C) 계산
            C = total_rating_sum / count_for_mean if count_for_mean > 0 else 0
            m = 10  # 최소 리뷰 수 기준
            
            # 3. 가중 평점 계산 및 정렬
            sorted_airlines = sorted(
                all_airlines, 
                key=lambda a: self._calculate_weighted_rating(a, C, m), 
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
    
    async def get_popular_airlines_weekly(
        self, year: int, month: int, week: int, limit: int = 5
    ) -> List[Airline]:
        """
        특정 연/월/주차 기준 인기 항공사 조회
        
        Args:
            year: 연도
            month: 월
            week: 주차 (1주차: 1~7일, 2주차: 8~14일 ...)
            limit: 반환할 최대 항공사 수
            
        Returns:
            인기 항공사 목록 (순위 포함)
        """
        try:
            start_date, end_date = self._get_week_date_range(year, month, week)

            # 1) 해당 기간 리뷰 조회
            query = (
                self.reviews_collection.where("createdAt", ">=", start_date)
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
                return[]

            # 3) 항공사 메타데이터 조회
            codes = list(aggregates.keys())
            airline_docs = await run_in_threadpool(lambda: self._fetch_airline_docs(codes))

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
            sorted_airlines = sorted(
                all_airlines,
                key=lambda a: self._calculate_weighted_rating(a, C, m),
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
            raise DatabaseError(message=f"주차별 인기 항공사 조회 중 오류 발생: {e}")
    
    async def get_airline_detail(self, airline_code: str) -> Optional[AirlineDetail]:
        """
        항공사 상세 정보 조회 (레거시, AirlineDetail 모델 사용)
        
        Args:
            airline_code: 항공사 코드
            
        Returns:
            항공사 상세 정보 (없으면 None)
        """
        try:
            doc_ref = self.airlines_collection.document(airline_code)
            doc = await run_in_threadpool(doc_ref.get)
            
            if not doc.exists:
                return None
            
            data = doc.to_dict()
            
            # 전체 평균 평점 계산
            avg_ratings = data.get("averageRatings", {})
            if avg_ratings:
                overall_rating = sum(avg_ratings.values()) / len(avg_ratings)
            else:
                overall_rating = 0.0
            
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
    
    async def get_airline_statistics(self, airline_code: str) -> Optional[AirlineSchema]:
        """
        항공사의 집계된 통계 정보를 조회합니다.
        Cloud Function에 의해 자동 업데이트되는 데이터입니다.
        
        Args:
            airline_code: 항공사 코드
            
        Returns:
            AirlineSchema (없으면 None)
        """
        try:
            doc_ref = self.airlines_collection.document(airline_code)
            doc = await run_in_threadpool(doc_ref.get)
            
            if not doc.exists:
                return None
            
            data = doc.to_dict()
            
            # Firestore에 저장된 overallRating이 있으면 우선 사용, 없으면 계산
            if "overallRating" in data and data["overallRating"] is not None:
                overall_rating = data["overallRating"]
            else:
                # 전체 평균 평점 계산 (overallRating이 없는 경우에만)
                avg_ratings = data.get("averageRatings", {})
                if avg_ratings:
                    overall_rating = round(sum(avg_ratings.values()) / len(avg_ratings), 2)
                else:
                    overall_rating = 0.0
                # 계산한 값을 data에 저장
                data["overallRating"] = overall_rating
            
            # overallRating 필드가 data에 확실히 포함되도록 보장
            data["overallRating"] = overall_rating
            
            return AirlineSchema(**data)
        except Exception as e:
            if isinstance(e, CustomException):
                raise e
            raise DatabaseError(message=f"항공사 통계 조회 중 오류 발생: {e}")
    
    # Private helper methods
    
    @staticmethod
    def _get_week_date_range(year: int, month: int, week: int) -> tuple[datetime, datetime]:
        """
        특정 연/월의 주차(start, end)를 UTC 기준으로 계산
        
        Args:
            year: 연도
            month: 월
            week: 주차
            
        Returns:
            (start_date, end_date) 튜플
        """
        if week < 1:
            raise ValueError("week는 1 이상이어야 합니다.")
        start = datetime(year, month, 1, tzinfo=timezone.utc) + timedelta(days=(week - 1) * 7)
        end = start + timedelta(days=7)
        return start, end
    
    def _fetch_airline_docs(self, codes: List[str]) -> Dict:
        """
        여러 항공사 문서를 한번에 조회
        
        Args:
            codes: 항공사 코드 리스트
            
        Returns:
            코드를 키로 하는 문서 딕셔너리
        """
        result = {}
        for c in codes:
            result[c] = self.airlines_collection.document(c).get()
        return result
