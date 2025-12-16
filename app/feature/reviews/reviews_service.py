"""
리뷰 관련 비즈니스 로직
"""

import json
from typing import List, Optional, Tuple
from datetime import datetime, timedelta, timezone
from fastapi.concurrency import run_in_threadpool
from google.cloud.firestore_v1.base_query import FieldFilter

from app.core.firebase import FirebaseService
from app.feature.reviews.reviews_schemas import (
    ReviewSchema,
    ReviewFilterRequest,
    FilteredReviewsResponse,
    DetailedReviewsResponse,
    BIMOSummaryResponse,
    AirlineReviewsResponse,
)
from app.feature.reviews.review_filter_service import ReviewFilterService
from app.feature.reviews.review_summary_service import ReviewSummaryService
from app.core.exceptions.exceptions import (
    DatabaseError,
    ReviewNotFoundError,
    CustomException,
)


class ReviewsService:
    """리뷰 관련 비즈니스 로직을 처리하는 서비스 클래스"""
    
    def __init__(
        self, 
        firebase_service: FirebaseService,
        filter_service: ReviewFilterService,
        summary_service: ReviewSummaryService
    ):
        """
        ReviewsService 초기화
        
        Args:
            firebase_service: Firebase 서비스 인스턴스
            filter_service: 리뷰 필터링 서비스
            summary_service: 리뷰 요약 서비스
        """
        self.db = firebase_service.db
        self.reviews_collection = self.db.collection("reviews")
        self.airlines_collection = self.db.collection("airlines")
        self.filter_service = filter_service
        self.summary_service = summary_service
    
    async def get_reviews_by_airline(self, airline_code: str, limit: int = 10) -> List[ReviewSchema]:
        """
        항공사 코드로 리뷰를 조회합니다.
        
        Args:
            airline_code: 항공사 코드 (예: "KE", "OZ")
            limit: 조회할 리뷰 개수 (기본값: 10)
            
        Returns:
            리뷰 목록
        """
        try:
            query = self.reviews_collection.where(filter=FieldFilter("airlineCode", "==", airline_code)).limit(limit)
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

    async def get_review_by_id(self, review_id: str) -> ReviewSchema:
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
            doc_ref = self.reviews_collection.document(review_id)
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
        self,
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
        reviews = await self.get_reviews_by_airline(airline_code, limit=limit)
        
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
        
        return await self.summary_service.summarize_reviews_text(reviews, airline_name)

    async def get_airline_reviews_summary(
        self,
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
        reviews = await self.get_reviews_by_airline(airline_code, limit=100)
        
        if not reviews:
            return {
                "airline_code": airline_code,
                "airline_name": airline_name or airline_code,
                "summary": f"{airline_name or airline_code} 항공사에 대한 리뷰가 아직 없습니다.",
                "review_count": 0
            }
        
        summary = await self.summarize_reviews(airline_code, airline_name, limit=50)
        
        return {
            "airline_code": airline_code,
            "airline_name": airline_name or airline_code,
            "summary": summary,
            "review_count": len(reviews)
        }







    async def get_filtered_reviews(
        self,
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
                lambda: self.airlines_collection.document(airline_code).get()
            )
            
            if not airline_doc.exists:
                raise DatabaseError(message=f"항공사를 찾을 수 없습니다: {airline_code}")
            
            airline_data = airline_doc.to_dict()
            airline_name = airline_data.get("airlineName", airline_code)
            
            # 2. 모든 리뷰 조회
            query = self.reviews_collection.where(filter=FieldFilter("airlineCode", "==", airline_code))
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
            
            # 4. 필터링 적용 (ReviewFilterService 위임)
            filtered_reviews = self.filter_service.filter_reviews(all_reviews, filter_request)
            
            # 5. 정렬 적용 (ReviewFilterService 위임)
            filtered_reviews = self.filter_service.sort_reviews(filtered_reviews, sort)
            
            # 6. 페이지네이션 적용 (ReviewFilterService 위임)
            paginated_reviews, has_more = self.filter_service.paginate_reviews(filtered_reviews, limit, offset)
            
            return FilteredReviewsResponse(
                airline_code=airline_code,
                airline_name=airline_name,
                total_count=len(filtered_reviews),
                reviews=paginated_reviews,
                has_more=has_more
            )
        except Exception as e:
            if isinstance(e, CustomException):
                raise e
            raise DatabaseError(message=f"필터링된 리뷰 조회 중 오류 발생: {e}")

    async def get_airline_reviews_page(
        self,
        airline_code: str,
        sort: str = "latest",
        limit: int = 20,
        offset: int = 0
    ) -> AirlineReviewsResponse:
        """
        항공사 리뷰 페이지 정보를 조회합니다.
        
        Args:
            airline_code: 항공사 코드
            sort: 정렬 옵션 (latest, recommended, rating_high, rating_low)
            limit: 조회할 리뷰 개수
            offset: 오프셋
            
        Returns:
            AirlineReviewsResponse (평점 정보 + 리뷰 목록)
        """
        try:
            # 1. 항공사 정보 조회
            airline_doc = await run_in_threadpool(
                lambda: self.airlines_collection.document(airline_code).get()
            )
            
            if not airline_doc.exists:
                raise DatabaseError(message=f"항공사를 찾을 수 없습니다: {airline_code}")
            
            airline_data = airline_doc.to_dict()
            airline_name = airline_data.get("airlineName", airline_code)
            
            # 2. 평점 정보 추출
            avg_ratings = airline_data.get("averageRatings", {})
            overall_rating = airline_data.get("overallRating", 0.0)
            
            # 전체 평점이 없으면 카테고리별 평균으로 계산
            if not overall_rating and avg_ratings:
                overall_rating = round(sum(avg_ratings.values()) / len(avg_ratings), 2)
            
            # 3. 모든 리뷰 조회
            query = self.reviews_collection.where(filter=FieldFilter("airlineCode", "==", airline_code))
            docs = await run_in_threadpool(lambda: list(query.stream()))
            
            # 4. ReviewSchema로 변환
            all_reviews = []
            for doc in docs:
                try:
                    data = doc.to_dict()
                    data["id"] = doc.id
                    review = ReviewSchema(**data)
                    all_reviews.append(review)
                except (ValueError, TypeError, KeyError):
                    continue  # 스키마 변환 실패 시 스킵
            
            # 5. 정렬 적용 (ReviewFilterService 위임)
            sorted_reviews = self.filter_service.sort_reviews(all_reviews, sort)
            
            # 6. 페이지네이션 적용 (ReviewFilterService 위임)
            paginated_reviews, has_more = self.filter_service.paginate_reviews(sorted_reviews, limit, offset)
            
            return AirlineReviewsResponse(
                airline_code=airline_code,
                airline_name=airline_name,
                overall_rating=overall_rating,
                total_reviews=total_reviews,
                average_ratings=avg_ratings,
                reviews=paginated_reviews,
                has_more=has_more
            )
        except Exception as e:
            if isinstance(e, CustomException):
                raise e
            raise DatabaseError(message=f"항공사 리뷰 페이지 조회 중 오류 발생: {e}")

    async def get_detailed_reviews_page(
        self,
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
            filtered_response = await self.get_filtered_reviews(
                airline_code=airline_code,
                filter_request=filter_request,
                sort=sort,
                limit=limit,
                offset=offset
            )
            
            # 항공사 정보 및 평점 조회
            airline_doc = await run_in_threadpool(
                lambda: self.airlines_collection.document(airline_code).get()
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
                # imageUrls(복수) 기준으로 갤러리 구성
                for u in (review.imageUrls or []):
                    if isinstance(u, str) and u.strip():
                        photo_urls.append(u.strip())
            
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

    async def create_review(self, review_data: ReviewSchema, user_id: str) -> ReviewSchema:
        """
        새로운 리뷰를 생성합니다.
        
        Args:
            review_data: 리뷰 데이터
            user_id: 사용자 ID (인증용)
            
        Returns:
            생성된 리뷰
            
        Raises:
            DatabaseError: 리뷰 생성 중 오류 발생 시
        """
        try:
            # 사용자 ID 검증
            if review_data.userId != user_id:
                raise DatabaseError(message="사용자 ID가 일치하지 않습니다.")
            
            # 리뷰 데이터 준비
            review_dict = review_data.model_dump(exclude={"id"})
            review_dict["createdAt"] = datetime.now(timezone.utc)
            
            # Firestore에 리뷰 저장
            doc_ref = self.reviews_collection.document()
            await run_in_threadpool(lambda: doc_ref.set(review_dict))
            
            # 생성된 리뷰 조회
            created_doc = await run_in_threadpool(doc_ref.get)
            created_data = created_doc.to_dict()
            created_data["id"] = created_doc.id
            created_review = ReviewSchema(**created_data)
            
            return created_review
        except Exception as e:
            if isinstance(e, CustomException):
                raise e
            raise DatabaseError(message=f"리뷰 생성 중 오류 발생: {e}")

    async def update_review(self, review_id: str, review_data: ReviewSchema, user_id: str) -> ReviewSchema:
        """
        기존 리뷰를 수정합니다.
        
        Args:
            review_id: 리뷰 ID
            review_data: 수정할 리뷰 데이터
            user_id: 사용자 ID (인증용)
            
        Returns:
            수정된 리뷰
            
        Raises:
            ReviewNotFoundError: 리뷰를 찾을 수 없을 때
            DatabaseError: 권한이 없거나 오류 발생 시
        """
        try:
            # 기존 리뷰 조회
            doc_ref = self.reviews_collection.document(review_id)
            doc = await run_in_threadpool(doc_ref.get)
            
            if not doc.exists:
                raise ReviewNotFoundError(review_id=review_id)
            
            existing_data = doc.to_dict()
            
            # 사용자 권한 확인
            if existing_data.get("userId") != user_id:
                raise DatabaseError(message="리뷰를 수정할 권한이 없습니다.")
            
            # 항공사 코드 변경 여부 확인
            old_airline_code = existing_data.get("airlineCode")
            new_airline_code = review_data.airlineCode
            airline_changed = old_airline_code != new_airline_code
            
            # 리뷰 데이터 업데이트
            update_dict = review_data.model_dump(exclude={"id", "userId", "createdAt"})
            await run_in_threadpool(lambda: doc_ref.update(update_dict))
            
            # 수정된 리뷰 조회
            updated_doc = await run_in_threadpool(doc_ref.get)
            updated_data = updated_doc.to_dict()
            updated_data["id"] = updated_doc.id
            updated_review = ReviewSchema(**updated_data)
            
            return updated_review
        except (ReviewNotFoundError, DatabaseError):
            raise
        except Exception as e:
            raise DatabaseError(message=f"리뷰 수정 중 오류 발생: {e}")

    async def delete_review(self, review_id: str, user_id: str) -> dict:
        """
        리뷰를 삭제합니다.
        
        Args:
            review_id: 리뷰 ID
            user_id: 사용자 ID (인증용)
            
        Returns:
            삭제 성공 메시지
            
        Raises:
            ReviewNotFoundError: 리뷰를 찾을 수 없을 때
            DatabaseError: 권한이 없거나 오류 발생 시
        """
        try:
            # 기존 리뷰 조회
            doc_ref = self.reviews_collection.document(review_id)
            doc = await run_in_threadpool(doc_ref.get)
            
            if not doc.exists:
                raise ReviewNotFoundError(review_id=review_id)
            
            existing_data = doc.to_dict()
            
            # 사용자 권한 확인
            if existing_data.get("userId") != user_id:
                raise DatabaseError(message="리뷰를 삭제할 권한이 없습니다.")
            
            airline_code = existing_data.get("airlineCode")
            
            # 리뷰 삭제
            await run_in_threadpool(doc_ref.delete)
            
            return {
                "message": "리뷰가 성공적으로 삭제되었습니다.",
                "review_id": review_id
            }
        except (ReviewNotFoundError, DatabaseError):
            raise
        except Exception as e:
            raise DatabaseError(message=f"리뷰 삭제 중 오류 발생: {e}")

    async def _update_airline_statistics(self, airline_code: str):
        """
        항공사 코드 통계를 재계산하고 업데이트합니다.
        
        Args:
            airline_code: 항공사 코드
        """
        try:
            # 해당 항공사의 모든 리뷰 조회
            query = self.reviews_collection.where(filter=FieldFilter("airlineCode", "==", airline_code))
            docs = await run_in_threadpool(lambda: list(query.stream()))
            
            if not docs:
                # 리뷰가 없으면 통계 초기화
                stats = {
                    "totalReviews": 0,
                    "totalRatingSums": {},
                    "averageRatings": {},
                    "ratingBreakdown": {},
                    "overallRating": 0.0
                }
            else:
                # 카테고리별 평점 합계
                rating_sums = {
                    "seatComfort": 0,
                    "inflightMeal": 0,
                    "service": 0,
                    "cleanliness": 0,
                    "checkIn": 0
                }
                
                # 전체 평점 합계
                overall_rating_sum = 0.0
                
                # 평점 분포 (1점~5점)
                rating_breakdown = {
                    "1": 0,
                    "2": 0,
                    "3": 0,
                    "4": 0,
                    "5": 0
                }
                
                # 리뷰 데이터 집계
                for doc in docs:
                    review_data = doc.to_dict()
                    
                    # 카테고리별 평점 누적
                    ratings = review_data.get("ratings", {})
                    for category in rating_sums.keys():
                        rating_sums[category] += ratings.get(category, 0)
                    
                    # 전체 평점 누적
                    overall = review_data.get("overallRating", 0.0)
                    overall_rating_sum += overall
                    
                    # 평점 분포 계산 (반올림)
                    rating_key = str(round(overall))
                    if rating_key in rating_breakdown:
                        rating_breakdown[rating_key] += 1
                
                # 평균 계산
                total_reviews = len(docs)
                average_ratings = {
                    category: round(sum_value / total_reviews, 2)
                    for category, sum_value in rating_sums.items()
                }
                
                overall_rating = round(overall_rating_sum / total_reviews, 2)
                
                stats = {
                    "totalReviews": total_reviews,
                    "totalRatingSums": rating_sums,
                    "averageRatings": average_ratings,
                    "ratingBreakdown": rating_breakdown,
                    "overallRating": overall_rating
                }
            
            # airlines 컬렉션 업데이트
            airline_ref = self.airlines_collection.document(airline_code)
            await run_in_threadpool(lambda: airline_ref.update(stats))
            
        except Exception as e:
            # 통계 업데이트 실패는 로그만 남기고 계속 진행
            print(f"항공사 통계 업데이트 실패 ({airline_code}): {e}")

    async def _update_bimo_summary(self, airline_code: str):
        """
        항공사의 BIMO AI 요약을 재생성하고 airlines 컬렉션에 저장합니다.
        
        Args:
            airline_code: 항공사 코드
        """
        try:
            # BIMO 요약 생성
            summary_response = await self.generate_bimo_summary(airline_code)
            
            # airlines 컬렉션에 저장할 데이터
            bimo_data = {
                "bimoSummary": {
                    "goodPoints": summary_response.good_points,
                    "badPoints": summary_response.bad_points,
                    "reviewCount": summary_response.review_count,
                    "lastUpdated": datetime.now(timezone.utc)
                }
            }
            
            # airlines 컬렉션 업데이트
            airline_ref = self.airlines_collection.document(airline_code)
            await run_in_threadpool(lambda: airline_ref.update(bimo_data))
            
            print(f"✓ BIMO 요약 업데이트 완료 ({airline_code}): Good {len(summary_response.good_points)}개, Bad {len(summary_response.bad_points)}개")
            
        except Exception as e:
            # BIMO 요약 업데이트 실패는 로그만 남기고 계속 진행
            print(f"BIMO 요약 업데이트 실패 ({airline_code}): {e}")

    async def get_reviews_by_user(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
        sort: str = "latest"
    ):
        """
        사용자가 작성한 리뷰를 조회합니다.
        
        Args:
            user_id: 사용자 ID
            limit: 조회할 리뷰 개수 (기본값: 20)
            offset: 오프셋 (페이지네이션용, 기본값: 0)
            sort: 정렬 옵션 (latest, rating_high, rating_low)
            
        Returns:
            사용자가 작성한 리뷰 응답 (total_count, reviews, has_more 포함)
            
        Raises:
            DatabaseError: 리뷰 조회 중 오류 발생 시
        """
        try:
            # Firestore 쿼리: userId로만 필터링 (정렬 없이)
            query = self.reviews_collection.where(filter=FieldFilter("userId", "==", user_id))
            
            # 모든 문서 조회
            docs = await run_in_threadpool(lambda: list(query.stream()))
            
            # ReviewSchema로 변환
            all_reviews = []
            for doc in docs:
                try:
                    review_data = doc.to_dict()
                    review_data["id"] = doc.id
                    all_reviews.append(ReviewSchema(**review_data))
                except (ValueError, TypeError, KeyError):
                    continue  # 스키마 변환 실패 시 스킵
            
            # Python에서 정렬 (Firestore 인덱스 불필요)
            if sort == "latest":
                all_reviews.sort(key=lambda x: x.createdAt, reverse=True)
            elif sort == "rating_high":
                all_reviews.sort(key=lambda x: x.overallRating, reverse=True)
            elif sort == "rating_low":
                all_reviews.sort(key=lambda x: x.overallRating)
            
            # 전체 개수
            total_count = len(all_reviews)
            
            # 페이지네이션 적용
            paginated_reviews = all_reviews[offset:offset + limit]
            has_more = offset + limit < total_count
            
            from app.feature.reviews.reviews_schemas import MyReviewsResponse
            
            return MyReviewsResponse(
                user_id=user_id,
                total_count=total_count,
                reviews=paginated_reviews,
                has_more=has_more
            )
            
        except Exception as e:
            if isinstance(e, CustomException):
                raise e
            raise DatabaseError(message=f"사용자 리뷰 조회 중 오류 발생: {e}")

    async def get_user_review_count(self, user_id: str) -> int:
        """
        사용자가 작성한 총 리뷰 개수를 조회합니다.
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            리뷰 개수
        """
        try:
            query = self.reviews_collection.where(filter=FieldFilter("userId", "==", user_id))
            docs = await run_in_threadpool(lambda: list(query.stream()))
            return len(docs)
        except Exception as e:
            if isinstance(e, CustomException):
                raise e
            raise DatabaseError(message=f"리뷰 개수 조회 중 오류 발생: {e}")

    async def increment_likes(self, review_id: str) -> dict:
        """
        리뷰의 좋아요 수를 1 증가시킵니다.
        
        Args:
            review_id: 리뷰 ID
            
        Returns:
            업데이트된 좋아요 수
            
        Raises:
            ReviewNotFoundError: 리뷰를 찾을 수 없을 때
            DatabaseError: 업데이트 중 오류 발생 시
        """
        try:
            doc_ref = self.reviews_collection.document(review_id)
            doc = await run_in_threadpool(doc_ref.get)
            
            if not doc.exists:
                raise ReviewNotFoundError(review_id=review_id)
            
            review_data = doc.to_dict()
            current_likes = review_data.get("likes", 0)
            new_likes = current_likes + 1
            
            # 좋아요 수 업데이트
            await run_in_threadpool(doc_ref.update, {"likes": new_likes})
            
            return {
                "review_id": review_id,
                "likes": new_likes
            }
            
        except ReviewNotFoundError:
            raise
        except Exception as e:
            if isinstance(e, CustomException):
                raise e
            raise DatabaseError(message=f"좋아요 업데이트 중 오류 발생: {e}")
