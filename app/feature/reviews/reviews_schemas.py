from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Optional, List, Dict
from datetime import datetime, timezone

class RatingsSchema(BaseModel):
    """리뷰에 포함되는 개별 항목의 평점"""
    seatComfort: int = Field(..., ge=1, le=5)
    inflightMeal: int = Field(..., ge=1, le=5)
    service: int = Field(..., ge=1, le=5)
    cleanliness: int = Field(..., ge=1, le=5)
    checkIn: int = Field(..., ge=1, le=5)

    model_config = ConfigDict(from_attributes=True)


class ReviewSummaryRequest(BaseModel):
    """리뷰 요약 요청 스키마"""
    airline_code: str = Field(..., description="항공사 코드 (예: KE, OZ)")
    airline_name: Optional[str] = Field(None, description="항공사 이름 (선택사항)")
    limit: Optional[int] = Field(50, ge=1, le=100, description="요약에 사용할 리뷰 개수")

    model_config = ConfigDict(from_attributes=True)


class ReviewSummaryResponse(BaseModel):
    """리뷰 요약 응답 스키마"""
    airline_code: str
    airline_name: str
    summary: str
    review_count: int

    model_config = ConfigDict(from_attributes=True)


class BIMOSummaryResponse(BaseModel):
    """BIMO 요약 응답 스키마 (Good/Bad 포인트 분리)"""
    airline_code: str
    airline_name: str
    good_points: List[str] = Field(..., description="장점 리스트")
    bad_points: List[str] = Field(..., description="단점 리스트")
    review_count: int

    model_config = ConfigDict(from_attributes=True)


class AirlineReviewsResponse(BaseModel):
    """항공사 리뷰 페이지 응답 스키마"""
    airline_code: str
    airline_name: str
    overall_rating: float
    total_reviews: int
    average_ratings: Dict[str, float] = Field(..., description="카테고리별 평균 평점")
    reviews: List["ReviewSchema"] = Field(..., description="리뷰 목록")
    has_more: bool = Field(..., description="더 많은 리뷰가 있는지 여부")

    model_config = ConfigDict(from_attributes=True)


class DetailedReviewsResponse(BaseModel):
    """상세 리뷰 페이지 응답 스키마"""
    airline_code: str
    airline_name: str
    overall_rating: float
    total_reviews: int
    average_ratings: Dict[str, float] = Field(..., description="카테고리별 평균 평점")
    photo_reviews: List[str] = Field(..., description="사진 리뷰 이미지 URL 리스트")
    photo_count: int = Field(..., description="사진 리뷰 개수")
    reviews: List["ReviewSchema"] = Field(..., description="리뷰 목록")
    has_more: bool = Field(..., description="더 많은 리뷰가 있는지 여부")

    model_config = ConfigDict(from_attributes=True)


class ReviewSchema(BaseModel):
    """
    사용자가 작성한 비행 리뷰를 나타냅니다.
    경로: reviews/{reviewId}
    """
    userId: str
    id: Optional[str] = None
    userNickname: str
    airlineCode: str
    airlineName: str
    route: str
    flightNumber: Optional[str] = None  # 항공편 번호 (예: "KE901")
    seatClass: Optional[str] = None  # 좌석 등급 (예: "이코노미", "비즈니스", "퍼스트", "프리미엄 이코노미")
    imageUrls: List[str] = Field(default_factory=list, description="리뷰 이미지 URL 리스트 (0-3개)")
    # 하위 호환성(deprecated): 예전 클라이언트/데이터는 imageUrl(단수)을 보낼 수 있음
    # - 입력은 허용하되, 내부적으로 imageUrls로 통합하고 응답/저장에서는 제외(exclude=True)
    imageUrl: Optional[str] = Field(
        default=None,
        description="(deprecated) 단일 리뷰 이미지 URL. 대신 imageUrls(리스트)를 사용하세요.",
        exclude=True,
    )
    ratings: RatingsSchema
    overallRating: float = Field(..., ge=1, le=5)
    text: str
    isVerified: bool = False
    likes: int = Field(0, description="좋아요 수", ge=0)
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="before")
    @classmethod
    def _normalize_image_fields(cls, data):
        """
        imageUrl(단수) / imageUrls(복수) 혼용을 imageUrls(복수)로 정규화합니다.
        - Firestore의 구버전 데이터나 구버전 클라이언트 요청을 깨지지 않게 하기 위함
        """
        if not isinstance(data, dict):
            return data

        image_urls = data.get("imageUrls")
        image_url = data.get("imageUrl")

        # imageUrls가 문자열로 들어오는 경우(실수/구버전) -> 리스트로 변환
        if isinstance(image_urls, str):
            image_urls = [image_urls]

        # imageUrls가 비어있고 imageUrl만 있으면 -> imageUrls로 승격
        if (not image_urls) and isinstance(image_url, str) and image_url.strip():
            image_urls = [image_url]

        # 최종 정리: 빈 값 제거 + 최대 3개 제한
        if isinstance(image_urls, list):
            cleaned = []
            for u in image_urls:
                if isinstance(u, str):
                    u = u.strip()
                    if u:
                        cleaned.append(u)
            data["imageUrls"] = cleaned[:3]

        return data

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "userId": "some_firebase_uid",
                "userNickname": "BIMO",
                "airlineCode": "KE",
                "airlineName": "대한항공",
                "route": "ICN-CDG",
                "ratings": {
                    "seatComfort": 5,
                    "inflightMeal": 4,
                    "service": 3,
                    "cleanliness": 3,
                    "checkIn": 4
                },
                "overallRating": 3.8,
                "text": "좌석은 편했지만 기내식이 아쉬웠어요.",
                "isVerified": True,
            }
        }
    )


class ReviewFilterRequest(BaseModel):
    """리뷰 필터링 요청 스키마"""
    departure_airport: Optional[str] = Field(None, description="출발 공항 코드 (예: ICN)")
    arrival_airport: Optional[str] = Field(None, description="도착 공항 코드 (예: CDG)")
    seat_class: Optional[str] = Field(None, description="좌석 등급: 전체, 프리미엄 이코노미, 이코노미, 비즈니스, 퍼스트")
    period: Optional[str] = Field(None, description="기간: 전체, 최근 3개월, 최근 6개월, 최근 1년")
    min_rating: Optional[int] = Field(None, ge=1, le=5, description="최소 평점 (1~5)")
    photo_only: Optional[bool] = Field(False, description="사진/동영상 리뷰만 보기")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "departure_airport": "ICN",
                "arrival_airport": "CDG",
                "seat_class": "이코노미",
                "period": "최근 3개월",
                "min_rating": 4,
                "photo_only": False
            }
        }
    )


class FilteredReviewsResponse(BaseModel):
    """필터링된 리뷰 응답 스키마"""
    airline_code: str
    airline_name: str
    total_count: int = Field(..., description="필터링된 전체 리뷰 개수")
    reviews: List[ReviewSchema] = Field(..., description="리뷰 목록")
    has_more: bool = Field(..., description="더 많은 리뷰가 있는지 여부")
    
    model_config = ConfigDict(from_attributes=True)


class MyReviewsResponse(BaseModel):
    """사용자가 작성한 리뷰 응답 스키마"""
    user_id: str = Field(..., description="사용자 ID")
    total_count: int = Field(..., description="전체 리뷰 개수")
    reviews: List[ReviewSchema] = Field(..., description="리뷰 목록")
    has_more: bool = Field(..., description="더 많은 리뷰가 있는지 여부")
    
    model_config = ConfigDict(from_attributes=True)


class ReviewVerificationResponse(BaseModel):
    """리뷰 인증 결과 응답 스키마"""
    isVerified: bool = Field(..., description="인증 성공 여부 (true: 인증됨, false: 인증 실패)")
    
    model_config = ConfigDict(from_attributes=True)
