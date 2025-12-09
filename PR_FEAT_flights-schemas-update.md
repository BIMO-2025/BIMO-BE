# feat: Add airline and flight search schemas with comprehensive data models

## 📋 개요

항공사 정보 및 항공편 검색 기능을 위한 포괄적인 데이터 모델 스키마를 추가했습니다. 항공사 집계 통계, 항공편 검색 요청/응답 스키마를 포함하여 데이터 구조를 명확하게 정의했습니다.

## ✨ 주요 변경 사항

### 1. 항공사 스키마 (`AirlineSchema`) 추가

항공사의 집계된 리뷰 데이터를 나타내는 스키마를 추가했습니다.

#### 기본 정보
- `airlineName`: 항공사 이름
- `airlineNameEn`: 영어 이름 (선택적)
- `country`: 본사 위치
- `hubAirport`: 허브 공항 코드 (예: "CDG")
- `hubAirportName`: 허브 공항 이름 (예: "파리 샤를 드골")
- `alliance`: 항공 동맹 (예: "SkyTeam", "Star Alliance", "oneworld")
- `type`: 항공사 타입 ("FSC" 또는 "LCC")
- `operatingClasses`: 운항 클래스 리스트
- `logoUrl`: 로고 이미지 URL
- `images`: 항공사 이미지 리스트

#### 집계 통계 (Cloud Function에 의해 자동 업데이트)
- `totalReviews`: 전체 리뷰 개수
- `totalRatingSums`: 카테고리별 평점 합계
- `averageRatings`: 카테고리별 평균 평점
- `ratingBreakdown`: 평점 분포 (1점~5점별 개수)
- `overallRating`: 전체 평점 (카테고리별 평균의 평균)

### 2. 항공편 검색 스키마 추가

#### `FlightSearchRequest`
항공편 검색 요청을 위한 스키마:
- `origin`: 출발지 공항 코드 (3자리, 예: "ICN", "JFK")
- `destination`: 도착지 공항 코드 (3자리)
- `departure_date`: 출발 날짜 (YYYY-MM-DD 형식)
- `adults`: 성인 승객 수 (1~9명)

#### `FlightOfferSchema`
검색된 항공편 제안 정보:
- `id`: 항공편 제안 ID
- `source`: 데이터 소스
- `instant_ticketing_required`: 즉시 발권 필요 여부
- `non_homogeneous`: 동일 항공사 여부
- `one_way`: 편도 여부
- `last_ticketing_date`: 마지막 발권일
- `number_of_bookable_seats`: 예약 가능한 좌석 수
- `itineraries`: 여정 정보 리스트
- `price`: 가격 정보
- `validating_airline_codes`: 유효한 항공사 코드 리스트
- `traveler_pricings`: 승객별 가격 정보

#### `SegmentSchema`
항공편 구간 정보:
- `departure`: 출발 정보 (공항 코드, 시간 등)
- `arrival`: 도착 정보 (공항 코드, 시간 등)
- `carrier_code`: 항공사 코드
- `number`: 항공편 번호
- `aircraft`: 항공기 정보 (선택적)
- `duration`: 비행 시간 (선택적)

#### `ItinerarySchema`
항공편 여정 정보:
- `duration`: 전체 여정 시간
- `segments`: 구간 정보 리스트

#### `PriceSchema`
항공편 가격 정보:
- `total`: 총 가격
- `base`: 기본 가격
- `currency`: 통화 코드 (예: USD, KRW)

#### `FlightSearchResponse`
항공편 검색 응답:
- `flight_offers`: 검색된 항공편 제안 리스트
- `count`: 검색된 항공편 개수

### 3. MyFlight 스키마 (`MyFlightSchema`)
사용자의 비행 기록을 나타내는 스키마:
- `flightNumber`: 항공편 번호
- `airlineCode`: 항공사 코드
- `departureTime`: 출발 시간
- `arrivalTime`: 도착 시간
- `status`: 상태 ("scheduled" 또는 "completed")
- `reviewId`: 연결된 리뷰 ID (선택적)

## 📁 변경된 파일

### `app/feature/flights/flights_schemas.py`
- `AirlineSchema` 클래스 추가
- `FlightSearchRequest` 클래스 추가
- `FlightOfferSchema` 클래스 추가
- `SegmentSchema` 클래스 추가
- `ItinerarySchema` 클래스 추가
- `PriceSchema` 클래스 추가
- `FlightSearchResponse` 클래스 추가
- `MyFlightSchema` 클래스 추가

## 🔧 기술적 세부사항

### 스키마 설계 원칙
1. **타입 안정성**: Pydantic을 사용한 데이터 검증
2. **문서화**: 각 필드에 대한 상세한 설명 포함
3. **확장성**: 선택적 필드를 통한 유연한 구조
4. **예시 데이터**: `json_schema_extra`를 통한 API 문서 예시 제공

### 데이터 모델 구조
```
AirlineSchema
├── 기본 정보 (이름, 위치, 동맹 등)
├── 집계 통계 (리뷰 개수, 평점 등)
└── 메타데이터 (이미지, 로고 등)

FlightSearchRequest
└── 검색 조건 (출발지, 도착지, 날짜, 인원)

FlightSearchResponse
└── FlightOfferSchema[]
    ├── ItinerarySchema[]
    │   └── SegmentSchema[]
    └── PriceSchema
```

## 📝 사용 예시

### 항공사 스키마 예시
```json
{
  "airlineName": "대한항공",
  "airlineNameEn": "Korean Air",
  "country": "대한민국",
  "hubAirport": "ICN",
  "hubAirportName": "인천국제공항",
  "alliance": "SkyTeam",
  "type": "FSC",
  "operatingClasses": ["이코노미", "비즈니스", "퍼스트"],
  "totalReviews": 1250,
  "averageRatings": {
    "seatComfort": 4.2,
    "inflightMeal": 3.84,
    "service": 4.4,
    "cleanliness": 4.08,
    "checkIn": 3.92
  },
  "overallRating": 4.1
}
```

### 항공편 검색 요청 예시
```json
{
  "origin": "ICN",
  "destination": "JFK",
  "departure_date": "2025-06-15",
  "adults": 1
}
```

## ✅ 테스트

- [ ] 스키마 유효성 검증 테스트 작성 필요
- [ ] API 엔드포인트와의 통합 테스트 작성 필요

## 🔗 관련 이슈

이 PR은 항공편 검색 기능 구현의 기초가 되는 스키마 정의 작업입니다.

## 📚 참고 문서

- [DATABASE_SCHEMA.md](../docs/DATABASE_SCHEMA.md)
- [IMPLEMENTATION_SUMMARY.md](../docs/IMPLEMENTATION_SUMMARY.md)
