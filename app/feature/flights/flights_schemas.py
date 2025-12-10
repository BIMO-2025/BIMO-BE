from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Literal, Optional, List
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
    logoUrl: Optional[str] = None
    totalReviews: int = 0
    totalRatingSums: Dict[str, int] = Field(default_factory=dict)
    averageRatings: Dict[str, float] = Field(default_factory=dict)
    ratingBreakdown: Dict[str, Dict[str, int]] = Field(default_factory=dict)
    overallRating: float = 0.0
    # 확장 필드 (상세 화면용)
    alliance: Optional[str] = Field(None, description="항공 동맹 (예: SkyTeam)")
    type: str = Field("FSC", description="FSC 또는 LCC")
    country: Optional[str] = Field(None, description="소속 국가")
    hubAirport: Optional[str] = Field(None, description="허브 공항 코드")
    hubAirportName: Optional[str] = Field(None, description="허브 공항 이름")
    operatingClasses: List[str] = Field(default_factory=list, description="운항 클래스 목록")
    images: List[str] = Field(default_factory=list, description="대표/갤러리 이미지 URL 리스트")
    description: Optional[str] = Field(None, description="항공사 설명")

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


# ===========================================================================
# 항공편 검색 관련 스키마
# ===========================================================================


class FlightSearchRequest(BaseModel):
    """
    항공편 검색 요청 스키마
    """
    origin: str = Field(..., description="출발지 공항 코드 (예: ICN, JFK)", min_length=3, max_length=3)
    destination: str = Field(..., description="도착지 공항 코드 (예: ICN, JFK)", min_length=3, max_length=3)
    departure_date: str = Field(..., description="출발 날짜 (YYYY-MM-DD 형식)", pattern=r"^\d{4}-\d{2}-\d{2}$")
    adults: int = Field(1, description="성인 승객 수", ge=1, le=9)
    sort_by: Optional[Literal["rating_desc", "review_count_desc", "price_asc"]] = Field(
        None, description="정렬 기준 (평점순: rating_desc, 리뷰많은순: review_count_desc, 가격순: price_asc)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "origin": "ICN",
                "destination": "JFK",
                "departure_date": "2025-06-15",
                "adults": 1
            }
        }
    )


class PriceSchema(BaseModel):
    """
    항공편 가격 정보
    """
    total: str = Field(..., description="총 가격")
    base: str = Field(..., description="기본 가격")
    currency: str = Field(..., description="통화 코드 (예: USD, KRW)")


class SegmentSchema(BaseModel):
    """
    항공편 구간 정보
    """
    departure: Dict = Field(..., description="출발 정보 (공항 코드, 시간 등)")
    arrival: Dict = Field(..., description="도착 정보 (공항 코드, 시간 등)")
    carrier_code: str = Field(..., alias="carrierCode", description="항공사 코드")
    number: str = Field(..., description="항공편 번호")
    aircraft: Optional[Dict] = Field(None, description="항공기 정보")
    duration: Optional[str] = Field(None, description="비행 시간")

    model_config = ConfigDict(populate_by_name=True)


class ItinerarySchema(BaseModel):
    """
    항공편 여정 정보
    """
    duration: str = Field(..., description="전체 여정 시간")
    segments: List[SegmentSchema] = Field(..., description="구간 정보 리스트")

    model_config = ConfigDict(populate_by_name=True)


class FlightOfferSchema(BaseModel):
    """
    검색된 항공편 제안 정보
    """
    id: str = Field(..., description="항공편 제안 ID")
    source: str = Field(..., description="데이터 소스")
    instant_ticketing_required: bool = Field(False, alias="instantTicketingRequired", description="즉시 발권 필요 여부")
    non_homogeneous: bool = Field(False, alias="nonHomogeneous", description="동일 항공사 여부")
    one_way: bool = Field(False, alias="oneWay", description="편도 여부")
    last_ticketing_date: Optional[str] = Field(None, alias="lastTicketingDate", description="마지막 발권일")
    number_of_bookable_seats: Optional[int] = Field(None, alias="numberOfBookableSeats", description="예약 가능한 좌석 수")
    itineraries: List[ItinerarySchema] = Field(..., description="여정 정보 리스트")
    price: PriceSchema = Field(..., description="가격 정보")

    validating_airline_codes: List[str] = Field(default_factory=list, description="유효한 항공사 코드 리스트")
    traveler_pricings: Optional[List[Dict]] = Field(None, description="승객별 가격 정보")
    
    # 추가된 필드
    airline_info: Optional[AirlineSchema] = Field(None, description="항공사 상세 정보 (평점, 리뷰 등)")
    is_direct: bool = Field(False, description="직항 여부")
    stopover_info: Optional[str] = Field(None, description="경유 정보 (예: '직항', '1회 경유')")



    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": "1",
                "source": "GDS",
                "one_way": False,
                "itineraries": [
                    {
                        "duration": "PT14H30M",
                        "segments": [
                            {
                                "departure": {
                                    "iataCode": "ICN",
                                    "at": "2025-06-15T10:00:00"
                                },
                                "arrival": {
                                    "iataCode": "JFK",
                                    "at": "2025-06-15T14:30:00"
                                },
                                "carrier_code": "KE",
                                "number": "901"
                            }
                        ]
                    }
                ],
                "price": {
                    "total": "1200.00",
                    "base": "1000.00",
                    "currency": "USD"
                }
            }
        }
    )


class FlightSearchResponse(BaseModel):
    """
    항공편 검색 응답 스키마
    """
    flight_offers: List[FlightOfferSchema] = Field(..., description="검색된 항공편 제안 리스트")
    count: int = Field(..., description="검색된 항공편 개수")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "flight_offers": [],
                "count": 0
            }
        }
    )


class LocationSchema(BaseModel):
    """
    공항 및 도시 정보 스키마
    """
    id: Optional[str] = Field(None, description="위치 ID")
    name: str = Field(..., description="위치 이름 (예: Incheon International Airport)")
    detailed_name: Optional[str] = Field(None, description="상세 이름 (예: SEOUL/ICN)")
    iata_code: str = Field(..., description="IATA 코드 (예: ICN)")
    geo_code: Optional[Dict] = Field(None, description="위도/경도 정보")
    address: Optional[Dict] = Field(None, description="주소 정보 (국가, 도시 등)")
    sub_type: str = Field(..., description="위치 유형 (AIRPORT, CITY)")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "AKL",
                "name": "AUCKLAND INTL",
                "detailed_name": "AUCKLAND/NZ",
                "iata_code": "AKL",
                "sub_type": "AIRPORT",
                "address": {
                    "cityName": "AUCKLAND",
                    "cityCode": "AKL",
                    "countryName": "NEW ZEALAND",
                    "countryCode": "NZ",
                    "regionCode": "OCEANIA"
                }
            }
        }
    )


class LocationSearchResponse(BaseModel):
    """
    위치 검색 응답 스키마
    """
    locations: List[LocationSchema] = Field(..., description="검색된 위치 목록")
    count: int = Field(..., description="검색된 위치 개수")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "locations": [
                    {
                        "name": "INCHEON INTL",
                        "iata_code": "ICN",
                        "sub_type": "AIRPORT"
                    },
                    {
                        "name": "SEOUL",
                        "iata_code": "SEL",
                        "sub_type": "CITY"
                    }
                ],
                "count": 2
            }
        }
    )
