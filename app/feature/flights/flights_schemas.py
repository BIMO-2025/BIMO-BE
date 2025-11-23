from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Literal, Optional
from datetime import datetime, timezone

class MyFlightSchema(BaseModel):
    """
    사용자의 비행 기록을 나타냅니다.
    경로: users/{userId}/myFlights/{myFlightId}
    """
    flightNumber: str
    airlineCode: str
    departureTime: datetime
    arrivalTime: datetime
    status: Literal["scheduled", "completed"]
    reviewId: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "flightNumber": "KE901",
                "airlineCode": "KE",
                "departureTime": "2025-12-25T13:45:00Z",
                "arrivalTime": "2025-12-25T18:20:00Z",
                "status": "scheduled",
            }
        }
    )

class AirlineSchema(BaseModel):
    """
    항공사의 집계된 리뷰 데이터를 나타냅니다.
    Cloud Function에 의해 업데이트됩니다.
    경로: airlines/{airlineCode}
    """
    airlineName: str
    totalReviews: int = 0
    totalRatingSums: Dict[str, int] = Field(default_factory=dict)
    averageRatings: Dict[str, float] = Field(default_factory=dict)
    ratingBreakdown: Dict[str, Dict[str, int]] = Field(default_factory=dict)

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "airlineName": "대한항공",
                "totalReviews": 1250,
                "totalRatingSums": {
                    "seatComfort": 5250,
                    "inflightMeal": 4800,
                    "service": 5500,
                    "cleanliness": 5100,
                    "checkIn": 4900
                },
                "averageRatings": {
                    "seatComfort": 4.2,
                    "inflightMeal": 3.84,
                    "service": 4.4,
                    "cleanliness": 4.08,
                    "checkIn": 3.92
                },
                "ratingBreakdown": {
                    "seatComfort": {"5": 800, "4": 300, "3": 100, "2": 30, "1": 20},
                    "inflightMeal": {"5": 600, "4": 400, "3": 200, "2": 40, "1": 10},
                }
            }
        }
    )
