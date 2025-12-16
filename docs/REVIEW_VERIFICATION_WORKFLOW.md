# 리뷰 인증 워크플로우

## 개요

사용자가 리뷰 작성 시 탑승권 이미지를 업로드하면, 서버가 자동으로 OCR을 통해 항공편 정보를 추출하고 사용자의 "마이 플라이트"에 저장된 항공편과 일치하는지 확인하여 인증(`isVerified`)을 처리합니다.

## 워크플로우

```
1. 사용자가 리뷰 작성 (이미지 포함)
   ↓
2. 서버가 이미지를 Base64로 변환
   ↓
3. OCR로 탑승권 정보 추출 (Gemini API)
   - 항공사 코드 (예: KE, OZ)
   - 항공편 번호 (예: KE901)
   - 출발 공항 코드 (예: ICN)
   - 도착 공항 코드 (예: JFK)
   - 출발 날짜 (예: 2025-12-20)
   - 좌석 등급 (선택사항)
   ↓
4. 사용자의 myFlights에서 일치하는 항공편 검색
   - status="completed"인 항공편만 확인
   - 최근 50개 항공편까지 확인
   ↓
5. 매칭 조건 확인
   ✅ 항공사 코드 일치
   ✅ 항공편 번호 일치
   ✅ 출발 공항 코드 일치
   ✅ 도착 공항 코드 일치
   ✅ 출발 날짜가 ±3일 이내
   ↓
6. 일치하는 항공편 발견 시
   → isVerified = True로 설정
   ↓
7. 일치하는 항공편 없음
   → isVerified = False로 설정 (기본값)
   ↓
8. 리뷰 저장 완료
```

## API 엔드포인트

### POST /reviews

리뷰 작성 시 이미지가 포함되어 있으면 자동으로 인증 프로세스가 실행됩니다.

**Request (multipart/form-data):**
```
- userId: string
- userNickname: string
- airlineCode: string
- airlineName: string
- route: string
- text: string
- ratings: string (JSON)
- overallRating: float
- flightNumber: string (optional)
- seatClass: string (optional)
- images: File[] (최대 3개)
```

**Response:**
```json
{
  "id": "review_id",
  "userId": "user_id",
  "isVerified": true,  // 인증 성공 시 true
  "imageUrls": ["data:image/jpeg;base64,..."],
  ...
}
```

## 매칭 로직 상세

### 1. OCR 정보 추출

`FlightInfoExtractor` 클래스가 Gemini API를 사용하여 탑승권 이미지에서 다음 정보를 추출합니다:

- `airline_code`: 항공사 코드 (예: "KE", "OZ")
- `flight_number`: 항공편 번호 (예: "KE901")
- `departure_airport`: 출발 공항 코드 (예: "ICN")
- `arrival_airport`: 도착 공항 코드 (예: "JFK")
- `departure_date`: 출발 날짜 (YYYY-MM-DD 형식)
- `seat_class`: 좌석 등급 (선택사항)
- `passenger_name`: 탑승객 이름 (선택사항)

### 2. 항공편 매칭

`FlightMatcher` 클래스가 추출된 정보와 myFlights의 항공편을 비교합니다:

#### 매칭 조건

1. **항공사 코드 일치**
   - 대소문자 무시
   - 예: "KE" == "ke" == "Ke"

2. **항공편 번호 일치**
   - 대소문자 무시
   - 항공사 코드 제거 후 비교
   - 예: "KE901" → "901" 비교

3. **출발 공항 코드 일치**
   - 대소문자 무시
   - 예: "ICN" == "icn"

4. **도착 공항 코드 일치**
   - 대소문자 무시
   - 경유 항공편의 경우 마지막 segment의 도착 공항과 비교

5. **출발 날짜 일치 (±3일 허용)**
   - 탑승권 날짜와 실제 출발 날짜가 ±3일 이내면 일치로 간주
   - 예: 탑승권 2025-12-20, 실제 출발 2025-12-22 → 일치

### 3. 인증 결과

- **인증 성공**: `isVerified = True`
- **인증 실패**: `isVerified = False` (기본값)
  - OCR 추출 실패
  - 일치하는 항공편 없음
  - 인증 프로세스 오류 발생

## 에러 처리

인증 프로세스 중 오류가 발생해도 리뷰 작성은 계속 진행됩니다:

- OCR 추출 실패 → `isVerified = False`
- 항공편 매칭 실패 → `isVerified = False`
- API 오류 → `isVerified = False` (로그 기록)

## 사용 예시

### JavaScript (클라이언트)

```javascript
const formData = new FormData();
formData.append('userId', 'user123');
formData.append('airlineCode', 'KE');
formData.append('route', 'ICN-JFK');
formData.append('text', '훌륭한 서비스!');
formData.append('ratings', JSON.stringify({
  seatComfort: 5, inflightMeal: 4, service: 5,
  cleanliness: 4, checkIn: 5
}));
formData.append('overallRating', 4.5);

// 탑승권 이미지 업로드
formData.append('images', boardingPassImageFile);

fetch('/reviews', {
  method: 'POST',
  headers: { 'Authorization': 'Bearer YOUR_TOKEN' },
  body: formData
})
.then(res => res.json())
.then(data => {
  if (data.isVerified) {
    console.log('✅ 리뷰가 인증되었습니다!');
  } else {
    console.log('❌ 리뷰 인증 실패 (myFlights에 일치하는 항공편 없음)');
  }
});
```

## 파일 구조

```
app/feature/reviews/
├── review_verification.py    # 인증 로직 (OCR 추출, 매칭)
├── reviews_router.py         # API 엔드포인트 (인증 통합)
└── reviews_schemas.py        # 스키마 정의 (isVerified 필드)
```

## 주요 클래스

### FlightInfoExtractor
- `extract_flight_info_from_image()`: 탑승권 이미지에서 항공편 정보 추출

### FlightMatcher
- `find_matching_flight()`: myFlights에서 일치하는 항공편 찾기
- `_matches_flight()`: 항공편 매칭 조건 확인

### verify_review_with_boarding_pass()
- 메인 인증 함수
- 이미지 리스트를 순회하며 인증 시도
- 성공 시 `True` 반환

## 주의사항

1. **Gemini API 할당량**: OCR은 Gemini API를 사용하므로 무료 할당량 제한이 있습니다.
2. **인증 실패해도 리뷰 작성 가능**: 인증 실패해도 리뷰는 정상적으로 저장됩니다.
3. **이미지 형식**: Base64 Data URL 형식만 지원합니다 (`data:image/jpeg;base64,...`).
4. **날짜 허용 오차**: 출발 날짜는 ±3일까지 허용됩니다 (탑승권 날짜와 실제 출발 날짜 차이 고려).

## 향후 개선 사항

- [ ] 인증 실패 시 사용자에게 피드백 제공
- [ ] 인증 성공 시 myFlights의 해당 항공편에 reviewId 자동 연결
- [ ] 인증 히스토리 로깅
- [ ] OCR 정확도 향상 (프롬프트 최적화)
- [ ] 여러 이미지에서 정보 추출 시도 (첫 번째 성공 시 중단)

