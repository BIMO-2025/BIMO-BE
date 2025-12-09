# 리뷰 시스템 구현 계획

## 📋 요구사항 정리

### 사용자 플로우
1. **항공편 검색** → 검색 결과 (항공사별 그룹화)
2. **검색 결과 클릭** → 항공사 리뷰 페이지 (평점, 카테고리별 평점, 리뷰 목록)
3. **평점 클릭** → 상세 리뷰 페이지 (전체 평점, 사진 갤러리, 개별 리뷰 목록)

### 필요한 기능

#### 1. 항공편 검색 결과 API (수정 필요)
- **현재**: `POST /flights/search` → Amadeus API 결과 그대로 반환
- **필요**: 항공사별로 그룹화하고, 각 항공사에 평점 정보 추가
- 항공사별로 직항/경유 구분
- 정렬 옵션: 평점 높은 순, 리뷰 많은 순

#### 2. 항공사 리뷰 페이지 API (새로 구현)
- `GET /airlines/{airline_code}/reviews`
- 응답 내용:
  - 전체 평점 (`overallRating`)
  - 카테고리별 평점 (`averageRatings`)
  - 리뷰 개수 (`totalReviews`)
  - 리뷰 목록 (정렬 옵션: 최신순, 추천순, 평점 높은 순, 평점 낮은 순)
  - BIMO 요약 (LLM 생성) - 별도 엔드포인트

#### 3. 상세 리뷰 페이지 API (새로 구현)
- `GET /reviews/detailed/{airline_code}`
- 응답 내용:
  - 전체 평점 (`overallRating`)
  - 카테고리별 평점 및 진행 바 표시용 데이터
  - 사진 리뷰 갤러리 (이미지 URL 리스트)
  - 개별 리뷰 목록 (정렬 옵션)
  - 각 리뷰: 사용자 정보, 평점, 비행 정보 (노선, 항공편 번호, 좌석 등급), 리뷰 텍스트, 좋아요 수, 이미지

#### 4. BIMO 요약 API (LLM 기반, 별도 엔드포인트)
- `POST /reviews/summarize` (기존)
- `GET /airlines/{airline_code}/summary` (새로 추가)
- 응답 형식:
  ```json
  {
    "airline_code": "AF",
    "airline_name": "에어프랑스",
    "good_points": ["만족스러운 기내식", "승무원 서비스 좋음", "지연 안 됨"],
    "bad_points": ["청결도가 아쉬움", "옆 자리 사람 시끄러움", "수속 시 문제 있었음"],
    "review_count": 1405
  }
  ```

#### 5. Mock 데이터 생성
- 각 항공사당 최소 **3개 이상**의 리뷰 생성
- 리뷰 필드:
  - `userId`, `userNickname`
  - `airlineCode`, `airlineName`
  - `route` (예: "ICN-CDG")
  - `flightNumber` (예: "KE901") - **추가 필요**
  - `seatClass` (예: "이코노미") - **추가 필요**
  - `imageUrl` (사진 리뷰용)
  - `ratings` (카테고리별 평점)
  - `overallRating`
  - `text` (리뷰 본문)
  - `isVerified`
  - `createdAt`
  - `likes` (좋아요 수) - **추가 필요**

---

## 🔨 구현 계획

### 1단계: ReviewSchema 확장

**파일**: `app/feature/reviews/reviews_schemas.py`

추가 필드:
```python
class ReviewSchema(BaseModel):
    # 기존 필드들...
    flightNumber: Optional[str] = None  # 항공편 번호 (예: "KE901")
    seatClass: Optional[str] = None  # 좌석 등급 (예: "이코노미", "비즈니스")
    likes: int = 0  # 좋아요 수
```

### 2단계: 항공편 검색 결과 API 수정

**파일**: `app/feature/flights/flights_service.py`, `flights_schemas.py`

새 스키마 추가:
```python
class AirlineGroupedResult(BaseModel):
    """항공사별 그룹화된 검색 결과"""
    airline_code: str
    airline_name: str
    airline_name_en: Optional[str]
    logo_url: Optional[str]
    rating: float  # 전체 평균 평점
    review_count: int
    flight_type: str  # "직항" 또는 "경유"
    via_airports: List[str]  # 경유 공항 리스트 (직항이면 빈 리스트)
    flight_offers: List[FlightOfferSchema]  # 해당 항공사의 항공편들

class FlightSearchGroupedResponse(BaseModel):
    """그룹화된 항공편 검색 응답"""
    results: List[AirlineGroupedResult]
    total_count: int
    sort_by: str  # "rating" 또는 "reviews"
```

**서비스 로직**:
1. Amadeus API로 항공편 검색
2. 항공사별로 그룹화
3. 각 항공사의 평점 정보 조회 (`airlines/{airlineCode}`)
4. 직항/경유 구분
5. 정렬 옵션 적용

### 3단계: 항공사 리뷰 페이지 API

**파일**: `app/feature/airlines/airline_router.py`

새 엔드포인트:
```python
@router.get("/{airline_code}/reviews", response_model=AirlineReviewsResponse)
async def get_airline_reviews_page(
    airline_code: str,
    sort: str = Query("latest", description="정렬 옵션: latest, recommended, rating_high, rating_low"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    항공사 리뷰 페이지 정보 조회
    
    - 평점 정보 (전체, 카테고리별)
    - 리뷰 목록 (정렬 옵션 지원)
    """
```

**스키마**:
```python
class AirlineReviewsResponse(BaseModel):
    airline_code: str
    airline_name: str
    overall_rating: float
    total_reviews: int
    average_ratings: Dict[str, float]  # 카테고리별 평균
    reviews: List[ReviewSchema]
    has_more: bool
```

### 4단계: 상세 리뷰 페이지 API

**파일**: `app/feature/reviews/reviews_router.py`

새 엔드포인트:
```python
@router.get("/detailed/{airline_code}", response_model=DetailedReviewsResponse)
async def get_detailed_reviews(
    airline_code: str,
    sort: str = Query("latest", description="정렬 옵션"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    항공사 상세 리뷰 페이지 정보 조회
    
    - 전체 평점, 카테고리별 평점
    - 사진 리뷰 갤러리
    - 개별 리뷰 목록
    """
```

**스키마**:
```python
class DetailedReviewsResponse(BaseModel):
    airline_code: str
    airline_name: str
    overall_rating: float
    total_reviews: int
    average_ratings: Dict[str, float]
    photo_reviews: List[str]  # 이미지 URL 리스트 (사진 있는 리뷰만)
    photo_count: int
    reviews: List[ReviewSchema]
    has_more: bool
```

### 5단계: BIMO 요약 API 개선

**파일**: `app/feature/reviews/reviews_service.py`, `reviews_schemas.py`

기존 `/reviews/summarize` 개선 + 새 엔드포인트 추가:
```python
@router.get("/airlines/{airline_code}/summary", response_model=BIMOSummaryResponse)
async def get_bimo_summary(airline_code: str):
    """
    BIMO 요약 정보 조회 (LLM 기반)
    Good/Bad 포인트 분리
    
    평점 관련 요청과 분리됨
    """
```

**스키마**:
```python
class BIMOSummaryResponse(BaseModel):
    airline_code: str
    airline_name: str
    good_points: List[str]  # 장점 리스트
    bad_points: List[str]  # 단점 리스트
    review_count: int
```

**LLM 프롬프트 설계**:
- 리뷰 데이터 수집
- Good/Bad 포인트 추출 요청
- JSON 형식으로 응답 받기

### 6단계: Mock 데이터 생성 스크립트 확장

**파일**: `scripts/seed_reviews_detailed.py` (새로 생성)

생성할 데이터:
- 각 항공사당 최소 3개 이상의 리뷰
- `flightNumber`, `seatClass`, `likes` 필드 포함
- 다양한 노선 (ICN-CDG, ICN-JFK, ICN-LAX 등)
- 사진 있는 리뷰와 없는 리뷰 혼합
- 다양한 평점 분포

### 7단계: 리뷰 서비스 로직 구현

**파일**: `app/feature/reviews/reviews_service.py`

새 함수들:
- `get_airline_reviews_page()`: 항공사 리뷰 페이지 데이터 조회
- `get_detailed_reviews_page()`: 상세 리뷰 페이지 데이터 조회
- `get_photo_reviews()`: 사진 리뷰만 조회
- `generate_bimo_summary()`: LLM으로 Good/Bad 포인트 생성 (개선)

---

## 📝 LLM 프롬프트 설계

### BIMO 요약용 프롬프트

```python
BIMO_SUMMARY_PROMPT = """
다음은 {airline_name} 항공사에 대한 {review_count}개의 리뷰입니다.

**카테고리별 평균 평점:**
- 좌석 편안함: {seat_comfort}/5.0
- 기내식 및 음료: {inflight_meal}/5.0
- 서비스: {service}/5.0
- 청결도: {cleanliness}/5.0
- 시간 준수도 및 수속: {check_in}/5.0

**리뷰 텍스트 샘플:**
{review_texts}

위 리뷰들을 분석하여 다음 형식의 JSON으로 응답해주세요:

{{
  "good_points": ["장점1", "장점2", "장점3"],
  "bad_points": ["단점1", "단점2", "단점3"]
}}

**요구사항:**
- good_points와 bad_points 각각 최소 3개, 최대 5개
- 각 포인트는 한 문장으로 간결하게 작성
- 실제 리뷰 내용을 기반으로 작성
- 객관적이고 균형잡힌 시각으로 작성
- 한국어로 작성

JSON 형식으로만 응답해주세요. 다른 설명은 포함하지 마세요.
"""
```

---

## 🎯 API 엔드포인트 정리

### 항공편 검색
- `POST /flights/search` (기존) - Amadeus 결과
- `POST /flights/search-grouped` (새로 추가) - 항공사별 그룹화 + 평점 정보

### 항공사 리뷰
- `GET /airlines/{airline_code}/reviews` - 항공사 리뷰 페이지
- `GET /airlines/{airline_code}/summary` - BIMO 요약 (LLM)

### 상세 리뷰
- `GET /reviews/detailed/{airline_code}` - 상세 리뷰 페이지

### 기존 (유지)
- `GET /reviews/airline/{airline_code}` - 항공사 리뷰 목록 (기본)
- `POST /reviews/summarize` - LLM 요약 (기존)

---

## ✅ 구현 우선순위 및 진행 상황

### ✅ 완료된 작업
1. **✅ ReviewSchema 확장** - `flightNumber`, `seatClass`, `likes` 필드 추가 완료
2. **✅ Mock 데이터 생성** - 각 항공사당 최소 3개 이상 리뷰 생성 스크립트 완료
3. **✅ 항공사 리뷰 페이지 API** - `GET /airlines/{airline_code}/reviews` 구현 완료
4. **✅ 상세 리뷰 페이지 API** - `GET /reviews/detailed/{airline_code}` 구현 완료
5. **✅ BIMO 요약 API 개선** - `GET /airlines/{airline_code}/summary` 구현 완료 (Good/Bad 포인트 분리)
6. **✅ LLM 프롬프트 작성** - Good/Bad 포인트 추출용 프롬프트 완성
7. **✅ LLM 임포트 오류 수정** - 대문자 `LLM` → 소문자 `llm`으로 통일

### 🔄 진행 중 / 미완료
6. **⏳ 항공편 검색 결과 그룹화** - 항공사별 그룹화 + 평점 추가 (아직 미구현)

---

## 📌 주의사항

1. **평점 API와 LLM API 분리**
   - 평점 관련: `GET /airlines/{airline_code}/reviews` - 빠른 응답
   - LLM 요약: `GET /airlines/{airline_code}/summary` - 별도 호출

2. **사진 리뷰 처리**
   - `imageUrl`이 있는 리뷰만 사진 갤러리에 포함
   - 상세 리뷰 페이지에서 사진 리뷰 개수 별도 표시

3. **정렬 옵션**
   - 최신순: `createdAt` 내림차순
   - 추천순: `likes` 내림차순
   - 평점 높은 순: `overallRating` 내림차순
   - 평점 낮은 순: `overallRating` 오름차순

4. **페이지네이션**
   - `limit`, `offset` 사용
   - `has_more` 필드로 더 보기 여부 표시

---

## 📝 구현 완료 내역

### 2025-01-XX 구현 완료
- ✅ `ReviewSchema` 모델 확장 (`flightNumber`, `seatClass`, `likes` 필드 추가)
- ✅ `AirlineReviewsResponse`, `DetailedReviewsResponse`, `BIMOSummaryResponse` 스키마 추가
- ✅ `get_airline_reviews_page()` 서비스 함수 구현 (정렬 옵션 지원)
- ✅ `get_detailed_reviews_page()` 서비스 함수 구현 (사진 갤러리 포함)
- ✅ `generate_bimo_summary()` 서비스 함수 구현 (LLM 기반 Good/Bad 포인트 분리)
- ✅ `GET /airlines/{airline_code}/reviews` API 엔드포인트 추가
- ✅ `GET /reviews/detailed/{airline_code}` API 엔드포인트 추가
- ✅ `GET /airlines/{airline_code}/summary` API 엔드포인트 추가
- ✅ Mock 데이터 생성 스크립트 개선 (각 항공사당 최소 3개 이상 리뷰, 새 필드 포함)
- ✅ LLM 임포트 경로 수정 (대문자 → 소문자)

### 구현된 API 엔드포인트 요약

#### 항공사 리뷰 페이지
```
GET /airlines/{airline_code}/reviews?sort=latest&limit=20&offset=0
```
- 전체 평점, 카테고리별 평점, 리뷰 목록 반환
- 정렬 옵션: `latest`, `recommended`, `rating_high`, `rating_low`

#### 상세 리뷰 페이지
```
GET /reviews/detailed/{airline_code}?sort=latest&limit=20&offset=0
```
- 전체 평점, 카테고리별 평점, 사진 갤러리, 개별 리뷰 목록 반환
- 사진 리뷰 개수 포함

#### BIMO 요약 (LLM)
```
GET /airlines/{airline_code}/summary
```
- Good/Bad 포인트를 분리하여 반환
- 평점 API와 별도로 호출 (느린 응답 예상)

