"""
리뷰 필터링 및 정렬 비즈니스 로직
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from app.feature.reviews.reviews_schemas import ReviewSchema, ReviewFilterRequest
from app.shared.datetime_utils import parse_iso_datetime


class ReviewFilterService:
    """리뷰 필터링 및 정렬을 담당하는 서비스 클래스"""

    def filter_reviews(
        self, 
        reviews: List[ReviewSchema], 
        filter_request: ReviewFilterRequest
    ) -> List[ReviewSchema]:
        """
        주어진 리뷰 목록에 필터링 조건을 적용합니다.
        
        Args:
            reviews: 전체 리뷰 목록
            filter_request: 필터 조건
            
        Returns:
            필터링된 리뷰 목록
        """
        filtered_reviews = []
        for review in reviews:
            if not self._matches_route_filter(review, filter_request.departure_airport, filter_request.arrival_airport):
                continue
            if not self._matches_seat_class_filter(review, filter_request.seat_class):
                continue
            if not self._matches_period_filter(review, filter_request.period):
                continue
            if not self._matches_rating_filter(review, filter_request.min_rating):
                continue
            if not self._matches_photo_filter(review, filter_request.photo_only):
                continue
            
            filtered_reviews.append(review)
            
        return filtered_reviews

    def sort_reviews(self, reviews: List[ReviewSchema], sort_option: str) -> List[ReviewSchema]:
        """
        주어진 리뷰 목록을 정렬합니다.
        
        Args:
            reviews: 리뷰 목록
            sort_option: 정렬 옵션 ("latest", "recommended", "rating_high", "rating_low", "likes_high")
            
        Returns:
            정렬된 리뷰 목록
        """
        sorted_reviews = list(reviews)  # 원본 보존을 위해 복사
        
        if sort_option == "latest":
            sorted_reviews.sort(key=lambda x: x.createdAt, reverse=True)
        elif sort_option == "recommended" or sort_option == "likes_high":
            # 추천순/좋아요순: 좋아요 수 내림차순 -> 최신순
            sorted_reviews.sort(key=lambda x: (x.likes, x.createdAt), reverse=True)
        elif sort_option == "rating_high":
            # 평점 높은 순: 평점 내림차순 -> 최신순
            sorted_reviews.sort(key=lambda x: (x.overallRating, x.createdAt), reverse=True)
        elif sort_option == "rating_low":
            # 평점 낮은 순: 평점 오름차순 -> 최신순
            sorted_reviews.sort(key=lambda x: (x.overallRating, -x.createdAt.timestamp()))
            
        return sorted_reviews

    def paginate_reviews(
        self, 
        reviews: List[ReviewSchema], 
        limit: int, 
        offset: int
    ) -> tuple[List[ReviewSchema], bool]:
        """
        리뷰 목록에 페이지네이션을 적용합니다.
        
        Args:
            reviews: 리뷰 목록
            limit: 가져올 개수
            offset: 시작 위치
            
        Returns:
            (페이지네이션된 리뷰 목록, 더 있는지 여부)
        """
        total_count = len(reviews)
        paginated_reviews = reviews[offset:offset + limit]
        has_more = offset + limit < total_count
        
        return paginated_reviews, has_more

    # =============================================================================
    # 내부 필터링 메서드
    # =============================================================================

    def _matches_route_filter(self, review: ReviewSchema, dep_airport: Optional[str], arr_airport: Optional[str]) -> bool:
        """리뷰가 경로 필터 조건에 맞는지 확인"""
        # 경로 정보 파싱 (예: "ICN-CDG")
        if not review.route or "-" not in review.route:
            # 경로 정보가 없거나 형식이 맞지 않으면 필터링에서 제외하지 않음 (보수적 접근)
            # 단, 필터가 지정된 경우 매칭 실패로 간주할 수도 있음. 
            # 여기서는 필터가 있으면 엄격하게 체크
            if dep_airport or arr_airport:
                return False
            return True
            
        try:
            origin, destination = review.route.split("-")
            origin = origin.strip()
            destination = destination.strip()
            
            if dep_airport and origin != dep_airport:
                return False
            if arr_airport and destination != arr_airport:
                return False
                
            return True
        except ValueError:
            return False

    def _matches_seat_class_filter(self, review: ReviewSchema, seat_class: Optional[str]) -> bool:
        """리뷰가 좌석 등급 필터 조건에 맞는지 확인"""
        if not seat_class or seat_class == "전체":
            return True
        
        # 데이터의 seatClass와 필터의 seat_class 비교 (대소문자 무시 등)
        # 데이터: "Economy", "Prestige", "First" 등 (항공사마다 다를 수 있음)
        # 필터: "이코노미", "비즈니스", "퍼스트", "프리미엄 이코노미" (한글 매핑 필요할 수 있음)
        
        if not review.seatClass:
            return False
            
        review_seat = review.seatClass.lower()
        filter_seat = seat_class.lower()
        
        # 단순 포함 여부나 매핑 로직
        if filter_seat == "이코노미" or filter_seat == "economy":
            return "economy" in review_seat and "premium" not in review_seat
        elif filter_seat == "프리미엄 이코노미" or filter_seat == "premium economy":
            return "premium" in review_seat
        elif filter_seat == "비즈니스" or filter_seat == "business":
            return "business" in review_seat or "prestige" in review_seat
        elif filter_seat == "퍼스트" or filter_seat == "first":
            return "first" in review_seat
            
        return filter_seat in review_seat

    def _matches_period_filter(self, review: ReviewSchema, period: Optional[str]) -> bool:
        """리뷰가 기간 필터 조건에 맞는지 확인"""
        if not period or period == "전체":
            return True
        
        # datetime_utils 사용
        now = datetime.now(timezone.utc)
        review_date = review.createdAt
        
        if isinstance(review_date, str):
            try:
                review_date = parse_iso_datetime(review_date)
            except (ValueError, AttributeError, TypeError):
                return True  # 파싱 실패 시 포함
        
        delta_map = {
            "최근 3개월": timedelta(days=90),
            "최근 6개월": timedelta(days=180),
            "최근 1년": timedelta(days=365),
        }
        
        delta = delta_map.get(period)
        if not delta:
            return True
        
        # review_date가 offset-naive일 경우 처리
        if review_date.tzinfo is None:
             review_date = review_date.replace(tzinfo=timezone.utc)
             
        return (now - review_date) <= delta

    def _matches_rating_filter(self, review: ReviewSchema, min_rating: Optional[int]) -> bool:
        """리뷰가 평점 필터 조건에 맞는지 확인"""
        if min_rating is None:
            return True
        
        return review.overallRating >= min_rating

    def _matches_photo_filter(self, review: ReviewSchema, photo_only: bool) -> bool:
        """리뷰가 사진 필터 조건에 맞는지 확인"""
        if not photo_only:
            return True

        # imageUrls(복수) 기준으로 판단
        return bool(getattr(review, "imageUrls", None)) and any(
            isinstance(u, str) and u.strip() for u in (review.imageUrls or [])
        )
