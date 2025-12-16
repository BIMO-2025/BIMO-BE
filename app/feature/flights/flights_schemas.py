from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Dict, Literal, Optional, List, Any
from datetime import datetime, timezone

class MyFlightSchema(BaseModel):
    """
    사용자의 비행 기록을 나타냅니다.
    경로: users/{userId}/myFlights/{myFlightId}
    
    직항 및 경유 항공편 모두 segments 필드로 처리합니다.
    segments[0]의 operating_carrier와 flight_number를 기본 항공편 정보로 사용합니다.
    """
    segments: List["SegmentDetailSchema"] = Field(..., min_length=1, description="항공편 구간 정보 리스트 (직항은 1개, 경유는 2개 이상)")
    departureTime: datetime = Field(..., description="전체 여정의 첫 출발 시간 (segments[0].departure.at과 일치해야 함)")
    arrivalTime: datetime = Field(..., description="전체 여정의 마지막 도착 시간 (segments[-1].arrival.at과 일치해야 함)")
    status: Literal["scheduled", "completed"]
    reviewId: Optional[str] = None
    departureAirport: Optional[str] = Field(None, description="출발 공항 코드 (예: ICN, segments[0].departure.iata_code와 일치해야 함)")
    arrivalAirport: Optional[str] = Field(None, description="도착 공항 코드 (예: JFK, segments[-1].arrival.iata_code와 일치해야 함)")
    hasStopover: Optional[bool] = Field(None, description="경유 여부 (segments가 2개 이상이면 True, 1개면 False, 자동 계산됨)")

    @model_validator(mode="after")
    def validate_segments(self):
        """segments 데이터 일관성 검증"""
        if len(self.segments) == 0:
            raise ValueError("segments는 최소 1개 이상이어야 합니다.")
        
        # 첫 번째 segment와 departureAirport/departureTime 일치 확인
        first_segment = self.segments[0]
        first_departure = first_segment.departure
        if isinstance(first_departure, dict):
            first_dep_iata = first_departure.get("iata_code") or first_departure.get("iataCode")
            first_dep_time = first_departure.get("at")
            
            if self.departureAirport and first_dep_iata and self.departureAirport != first_dep_iata:
                raise ValueError(f"첫 번째 segment의 출발 공항({first_dep_iata})이 departureAirport({self.departureAirport})와 일치하지 않습니다.")
            
            if first_dep_time:
                try:
                    if isinstance(first_dep_time, str):
                        first_dep_datetime = datetime.fromisoformat(first_dep_time.replace("Z", "+00:00"))
                    else:
                        first_dep_datetime = first_dep_time
                    if abs((first_dep_datetime - self.departureTime).total_seconds()) > 3600:  # 1시간 허용 오차
                        raise ValueError(f"첫 번째 segment의 출발 시간이 departureTime과 일치하지 않습니다.")
                except (ValueError, AttributeError):
                    pass  # 시간 형식이 다르면 검증 건너뛰기
        
        # 마지막 segment와 arrivalAirport/arrivalTime 일치 확인
        last_segment = self.segments[-1]
        last_arrival = last_segment.arrival
        if isinstance(last_arrival, dict):
            last_arr_iata = last_arrival.get("iata_code") or last_arrival.get("iataCode")
            last_arr_time = last_arrival.get("at")
            
            if self.arrivalAirport and last_arr_iata and self.arrivalAirport != last_arr_iata:
                raise ValueError(f"마지막 segment의 도착 공항({last_arr_iata})이 arrivalAirport({self.arrivalAirport})와 일치하지 않습니다.")
            
            if last_arr_time:
                try:
                    if isinstance(last_arr_time, str):
                        last_arr_datetime = datetime.fromisoformat(last_arr_time.replace("Z", "+00:00"))
                    else:
                        last_arr_datetime = last_arr_time
                    if abs((last_arr_datetime - self.arrivalTime).total_seconds()) > 3600:  # 1시간 허용 오차
                        raise ValueError(f"마지막 segment의 도착 시간이 arrivalTime과 일치하지 않습니다.")
                except (ValueError, AttributeError):
                    pass  # 시간 형식이 다르면 검증 건너뛰기
        
        # segments 간 연속성 검증
        for i in range(len(self.segments) - 1):
            current_segment = self.segments[i]
            next_segment = self.segments[i + 1]
            
            current_arrival = current_segment.arrival
            next_departure = next_segment.departure
            
            if isinstance(current_arrival, dict) and isinstance(next_departure, dict):
                current_arr_iata = current_arrival.get("iata_code") or current_arrival.get("iataCode")
                next_dep_iata = next_departure.get("iata_code") or next_departure.get("iataCode")
                
                if current_arr_iata and next_dep_iata and current_arr_iata != next_dep_iata:
                    raise ValueError(f"segment {i+1}의 도착 공항({current_arr_iata})과 segment {i+2}의 출발 공항({next_dep_iata})가 일치하지 않습니다.")
        
        # hasStopover 자동 설정
        if self.hasStopover is None:
            self.hasStopover = len(self.segments) > 1
        
        return self

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "segments": [
                    {
                        "operating_carrier": "KE",
                        "flight_number": "KE901",
                        "duration": "3H30M",
                        "departure": {
                            "iata_code": "ICN",
                            "at": "2025-12-25T10:00:00Z"
                        },
                        "arrival": {
                            "iata_code": "NRT",
                            "at": "2025-12-25T13:30:00Z"
                        }
                    },
                    {
                        "operating_carrier": "KE",
                        "flight_number": "KE001",
                        "duration": "11H00M",
                        "departure": {
                            "iata_code": "NRT",
                            "at": "2025-12-25T15:00:00Z"
                        },
                        "arrival": {
                            "iata_code": "JFK",
                            "at": "2025-12-25T20:30:00Z"
                        }
                    }
                ],
                "departureTime": "2025-12-25T10:00:00Z",
                "arrivalTime": "2025-12-25T20:30:00Z",
                "status": "scheduled",
                "departureAirport": "ICN",
                "arrivalAirport": "JFK",
                "hasStopover": True
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
    ratingBreakdown: Dict[str, Any] = Field(default_factory=dict)  # 유연하게 처리
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
    # BIMO 요약 (리뷰 기반 AI 요약)
    bimoSummary: Optional[Dict[str, Any]] = Field(None, description="BIMO AI 요약 (Good/Bad 포인트)")

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
                "destination": "LHR",
                "departure_date": "2025-12-30",
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
    number: str = Field(..., description="항공편 번호(KE901)")
    aircraft: Optional[Dict] = Field(None, description="항공기 정보(Boeing 737-800)")
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
    count: int = Field(..., description="검색된 항공편 개수")
    flight_offers: List[Dict] = Field(..., description="검색된 항공편 제안 리스트")
    airlines: List[AirlineSchema] = Field(default_factory=list, description="검색 결과에 포함된 항공사 정보 목록 (overallRating 내림차순 정렬)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "flight_offers": [],
                "count": 0,
                "airlines": []
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


# ===========================================================================
# 항공사 검색 관련 스키마 (Duffel API용)
# ===========================================================================


class AirlineSearchRequest(BaseModel):
    """
    항공사 검색 요청 스키마 (Duffel API용)
    """
    departure: str = Field(..., description="출발지 공항 IATA 코드 (예: ICN)", min_length=3, max_length=3)
    arrive: str = Field(..., description="도착지 공항 IATA 코드 (예: JFK)", min_length=3, max_length=3)
    departure_date: str = Field(..., description="출발 날짜 (YYYY-MM-DD 형식)", pattern=r"^\d{4}-\d{2}-\d{2}$")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "departure": "ICN",
                "arrive": "JFK",
                "departure_date": "2025-12-30"
            }
        }
    )


class SegmentDetailSchema(BaseModel):
    """
    각 구간의 상세 정보
    """
    operating_carrier: str = Field(..., description="운항 항공사 코드 (예: KE)")
    flight_number: str = Field(..., description="항공편명 (예: KE123)")
    duration: str = Field(..., description="구간 비행 시간 (예: PT14H30M 또는 14H30M)")
    departure: Dict = Field(..., description="출발 정보 (공항 코드, 시간 등)")
    arrival: Dict = Field(..., description="도착 정보 (공항 코드, 시간 등)")
    hasReview: Optional[bool] = Field(default=False, description="해당 항공편에 대한 리뷰 작성 여부")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "operating_carrier": "KE",
                "flight_number": "KE123",
                "duration": "14H30M",
                "departure": {
                    "iata_code": "ICN",
                    "at": "2025-12-30T10:00:00Z"
                },
                "arrival": {
                    "iata_code": "JFK",
                    "at": "2025-12-30T14:30:00Z"
                },
                "hasReview": False
            }
        }
    )


class AirlineSearchResponseItem(BaseModel):
    """
    항공사 검색 결과 항목
    """
    operating_carrier: str = Field(..., description="운항 항공사 코드 (owner가 아닌 실제 운항 항공사)")
    logo_symbol_url: Optional[str] = Field(None, description="항공사 로고 심볼 URL")
    has_stopover: bool = Field(..., description="경유 여부")
    flight_number: str = Field(..., description="항공편명 (첫 번째 구간의 항공편명, 예: KE123)")
    total_duration: str = Field(..., description="총 비행 시간 (예: 14H30M)")
    segments: List[SegmentDetailSchema] = Field(..., description="각 구간별 비행 시간 및 정보 (경유일 경우 여러 개)")
    overall_rating: Optional[float] = Field(None, description="항공사 전체 평점 (Firestore에서 조회, 없으면 null)")
    total_reviews: Optional[int] = Field(None, description="총 리뷰 수 (Firestore에서 조회, 없으면 null)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "operating_carrier": "KE",
                "logo_symbol_url": "https://assets.duffel.com/img/airlines/for-light-background/full-color-logo/KE.svg",
                "has_stopover": False,
                "flight_number": "KE123",
                "total_duration": "14H30M",
                "overall_rating": 4.2,
                "total_reviews": 1250,
                "segments": [
                    {
                        "operating_carrier": "KE",
                        "flight_number": "KE123",
                        "duration": "14H30M",
                        "departure": {
                            "iata_code": "ICN",
                            "at": "2025-12-30T10:00:00Z"
                        },
                        "arrival": {
                            "iata_code": "JFK",
                            "at": "2025-12-30T14:30:00Z"
                        }
                    }
                ]
            }
        }
    )


class AirlineSearchResponse(BaseModel):
    """
    항공사 검색 응답 스키마
    """
    count: int = Field(..., description="검색된 항공편 개수")
    results: List[AirlineSearchResponseItem] = Field(..., description="검색된 항공편 목록")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "count": 1,
                "results": [
                    {
                        "operating_carrier": "KE",
                        "logo_symbol_url": "https://assets.duffel.com/img/airlines/for-light-background/full-color-logo/KE.svg",
                        "has_stopover": False,
                        "flight_number": "KE123",
                        "total_duration": "14H30M",
                        "segments": [
                            {
                                "operating_carrier": "KE",
                                "flight_number": "KE123",
                                "duration": "14H30M",
                                "departure": {
                                    "iata_code": "ICN",
                                    "at": "2025-12-30T10:00:00Z"
                                },
                                "arrival": {
                                    "iata_code": "JFK",
                                    "at": "2025-12-30T14:30:00Z"
                                }
                            }
                        ]
                    }
                ]
            }
        }
    )


# ===========================================================================
# 공항 IATA 코드 검색 관련 스키마 (Duffel API용)
# ===========================================================================


class AirportIATASearchRequest(BaseModel):
    """
    공항 IATA 코드 검색 요청 스키마
    """
    location: str = Field(..., description="위치 정보 (도시명, 국가명 등, 예: 'Seoul' 또는 'Seoul South Korea')")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "location": "Seoul South Korea"
            }
        }
    )


class AirportIATAResult(BaseModel):
    """
    공항 IATA 코드 검색 결과 항목
    """
    iata_code: str = Field(..., description="공항 IATA 코드 (예: ICN)")
    city: Optional[str] = Field(None, description="도시명")
    country: Optional[str] = Field(None, description="국가명")
    name: Optional[str] = Field(None, description="공항명")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "iata_code": "ICN",
                "city": "Seoul",
                "country": "South Korea",
                "name": "Incheon International Airport"
            }
        }
    )


class AirportIATASearchResponse(BaseModel):
    """
    공항 IATA 코드 검색 응답 스키마
    """
    count: int = Field(..., description="검색된 공항 개수")
    results: List[AirportIATAResult] = Field(..., description="검색된 공항 목록")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "count": 1,
                "results": [
                    {
                        "iata_code": "ICN",
                        "city": "Seoul",
                        "country": "South Korea",
                        "name": "Incheon International Airport"
                    }
                ]
            }
        }
    )


# Forward reference 해결
MyFlightSchema.model_rebuild()
