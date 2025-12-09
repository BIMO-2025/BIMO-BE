# feat: Add detailed reviews page with photo gallery and sorting

## 📋 개요

항공사 상세 리뷰 페이지 기능을 추가하여 사용자가 항공사별 리뷰를 더 상세하게 조회할 수 있도록 개선했습니다. 사진 리뷰 갤러리, 다양한 정렬 옵션, 페이지네이션 기능을 포함합니다.

## ✨ 주요 변경 사항

### 1. 상세 리뷰 페이지 API 엔드포인트 추가
- **엔드포인트**: `GET /reviews/detailed/{airline_code}`
- **기능**: 항공사 코드를 기반으로 상세 리뷰 정보를 조회
- **응답 데이터**:
  - 전체 평점 (`overallRating`)
  - 카테고리별 평균 평점 (`averageRatings`)
  - 사진 리뷰 갤러리 (`photo_reviews`, `photo_count`)
  - 개별 리뷰 목록 (`reviews`)
  - 페이지네이션 정보 (`has_more`)

### 2. 정렬 옵션 지원
다음 5가지 정렬 옵션을 제공합니다:
- `latest`: 최신순 (기본값)
- `recommended`: 추천순 (좋아요 수 기준)
- `rating_high`: 평점 높은 순
- `rating_low`: 평점 낮은 순
- `likes_high`: 좋아요 많은 순 (recommended와 동일)

### 3. 필터링 기능 추가
다음 필터 옵션을 지원합니다:
- **노선 필터**: 출발 공항, 도착 공항 코드로 필터링
- **좌석 등급 필터**: 전체, 프리미엄 이코노미, 이코노미, 비즈니스, 퍼스트
- **기간 필터**: 전체, 최근 3개월, 최근 6개월, 최근 1년
- **평점 필터**: 최소 평점 설정 (1~5점)
- **사진 리뷰 필터**: 사진/동영상이 있는 리뷰만 조회

### 4. 페이지네이션 지원
- `limit`: 조회할 리뷰 개수 (기본값: 20, 최대: 100)
- `offset`: 오프셋 (기본값: 0)
- `has_more`: 더 많은 리뷰 존재 여부

### 5. 사진 리뷰 갤러리
- `imageUrl`이 있는 리뷰만 사진 갤러리에 포함
- 사진 리뷰 개수 별도 표시 (`photo_count`)

### 5. 버그 수정
- 중복된 라우트 정의 제거
- 불필요한 import 문 정리 (`HTTPException` 제거)

## 📁 변경된 파일

### `app/feature/reviews/reviews_schemas.py`
- `ReviewFilterRequest` 스키마 추가 (필터 조건)
- `FilteredReviewsResponse` 스키마 추가 (필터링된 리뷰 응답)

### `app/feature/reviews/reviews_router.py`
- `get_detailed_reviews()` 엔드포인트 추가 (필터링 및 정렬 지원)
- `get_filtered_reviews()` 엔드포인트 추가 (POST 방식)
- Query 파라미터로 필터 조건 전달 지원

### `app/feature/reviews/reviews_service.py`
- `get_detailed_reviews_page()` 함수 추가 (필터링 및 정렬 지원)
- `get_filtered_reviews()` 함수 추가
- 필터링 로직 구현:
  - 노선 필터 (`_matches_route_filter`)
  - 좌석 등급 필터 (`_matches_seat_class_filter`)
  - 기간 필터 (`_matches_period_filter`)
  - 평점 필터 (`_matches_rating_filter`)
  - 사진 필터 (`_matches_photo_filter`)
- 정렬 및 페이지네이션 로직 구현
- 사진 리뷰 수집 로직 구현

## 🔧 기술적 세부사항

### 서비스 레이어 (`reviews_service.py`)
```python
async def get_detailed_reviews_page(
    airline_code: str,
    sort: str = "latest",
    limit: int = 20,
    offset: int = 0
) -> DetailedReviewsResponse
```

**주요 로직**:
1. 항공사 정보 및 집계 통계 조회
2. 리뷰 조회 및 사진 URL 수집
3. 정렬 옵션에 따른 리뷰 정렬
4. 페이지네이션 적용
5. `DetailedReviewsResponse` 객체 생성 및 반환

### 스키마 (`reviews_schemas.py`)
- `DetailedReviewsResponse`: 상세 리뷰 페이지 응답 스키마
  - `photo_reviews`: 사진 리뷰 이미지 URL 리스트
  - `photo_count`: 사진 리뷰 개수
  - 기타 평점 및 리뷰 정보

## 📝 API 사용 예시

### 요청 (필터링 및 정렬 포함)
```http
GET /reviews/detailed/KE?departure_airport=ICN&arrival_airport=CDG&seat_class=이코노미&period=최근 3개월&min_rating=4&photo_only=false&sort=rating_high&limit=20&offset=0
```

### 요청 (POST 방식)
```http
POST /reviews/filtered/KE?sort=likes_high&limit=20&offset=0
Content-Type: application/json

{
  "departure_airport": "ICN",
  "arrival_airport": "CDG",
  "seat_class": "이코노미",
  "period": "최근 3개월",
  "min_rating": 4,
  "photo_only": false
}
```

### 응답
```json
{
  "airline_code": "KE",
  "airline_name": "대한항공",
  "overall_rating": 4.2,
  "total_reviews": 1250,
  "average_ratings": {
    "seatComfort": 4.2,
    "inflightMeal": 3.84,
    "service": 4.4,
    "cleanliness": 4.08,
    "checkIn": 3.92
  },
  "photo_reviews": [
    "https://example.com/photo1.jpg",
    "https://example.com/photo2.jpg"
  ],
  "photo_count": 2,
  "reviews": [...],
  "has_more": true
}
```

## ✅ 테스트

- [ ] 단위 테스트 작성 필요
- [ ] 통합 테스트 작성 필요
- [ ] API 엔드포인트 동작 확인

## 🔗 관련 이슈

이 PR은 리뷰 시스템 개선 작업의 일부입니다.

## 📝 커밋 내역

- fix: Remove duplicate route definition in reviews router
- feat: Add detailed reviews page service with photo gallery support
- feat: Add detailed reviews page API endpoint with sorting and pagination
- feat: Add filtering functionality (route, seat class, period, rating, photo)
- feat: Add sorting by rating and likes count

## 📚 참고 문서

- [IMPLEMENTATION_PLAN_REVIEWS.md](../docs/IMPLEMENTATION_PLAN_REVIEWS.md)
