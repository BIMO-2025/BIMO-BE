from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
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
    imageUrl: Optional[str] = None
    ratings: RatingsSchema
    overallRating: float = Field(..., ge=1, le=5)
    text: str
    isVerified: bool = False
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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
