# 데이터베이스 스키마 설계 문서

## 개요
BIMO-BE 프로젝트의 Firestore 데이터베이스 스키마 설계 문서입니다.

## 컬렉션 구조

### 1. myFlights
사용자의 비행 기록을 저장하는 컬렉션입니다.

**경로**: `users/{userId}/myFlights/{myFlightId}`

**필드**:
- `flightNumber`: (String) 항공편 번호 (예: "KE901")
- `airlineCode`: (String) 항공사 코드 (예: "KE")
- `departureTime`: (Timestamp) 출발 시간
- `arrivalTime`: (Timestamp) 도착 시간
- `status`: (String) 비행 상태
  - `"scheduled"`: 예정된 비행
  - `"completed"`: 완료된 비행
- `reviewId`: (String, Optional) 리뷰 ID (Foreign Key)
  - 이 비행에 대해 작성한 리뷰가 있다면 `reviews/{reviewId}` 참조

**인덱스**:
- `userId` (컬렉션 경로에서 자동)
- `status`
- `departureTime` (내림차순)
- `airlineCode`

**예시**:
```json
{
  "flightNumber": "KE901",
  "airlineCode": "KE",
  "departureTime": "2025-12-25T13:45:00Z",
  "arrivalTime": "2025-12-25T18:20:00Z",
  "status": "completed",
  "reviewId": "review_abc123"
}
```

---

### 2. reviews
사용자들이 작성한 항공사 리뷰를 저장하는 컬렉션입니다.

**경로**: `reviews/{reviewId}`

**필드**:
- `userId`: (String) 작성자 ID (users 컬렉션 참조)
- `userNickname`: (String) 작성자 닉네임
  - `users/{userId}` 컬렉션에서 복사하여 저장
  - 리뷰 목록 조회 시 JOIN 없이 바로 표시하기 위함
- `airlineCode`: (String) 항공사 코드 (예: "KE")
- `airlineName`: (String) 항공사 이름 (예: "대한항공")
- `route`: (String) 노선 정보 (예: "ICN-CDG")
- `imageUrl`: (String, Optional) 리뷰 이미지 URL
  - Firebase Storage에 업로드된 이미지 URL
- `ratings`: (Map) 세부 평점
  ```json
  {
    "seatComfort": 5,      // 좌석 편안함 (1-5)
    "inflightMeal": 4,     // 기내식 (1-5)
    "service": 3,          // 서비스 (1-5)
    "cleanliness": 3,      // 청결도 (1-5)
    "checkIn": 4           // 체크인 (1-5)
  }
  ```
- `overallRating`: (Number) 전체 평점 (1.0-5.0)
  - `ratings`의 각 카테고리 점수의 평균값
  - 자동 계산: `(seatComfort + inflightMeal + service + cleanliness + checkIn) / 5`
- `text`: (String) 리뷰 텍스트 본문
- `isVerified`: (Boolean) 인증 여부
  - `myFlights`와 연동된 비행 기록이 있는지 여부
  - `reviewId`가 `myFlights`의 `reviewId`와 일치하면 `true`
- `createdAt`: (Timestamp) 리뷰 작성 시간

**인덱스**:
- `airlineCode`
- `userId`
- `createdAt` (내림차순)
- `overallRating` (내림차순)
- `isVerified`

**이미지 처리 로직**:
1. 사용자가 이미지 업로드 요청
2. Firebase Storage에 이미지 업로드
   - 경로: `reviews/{reviewId}/images/{imageId}.{ext}`
3. 업로드 성공 시 URL 반환
4. `imageUrl` 필드에 저장

**예시**:
```json
{
  "userId": "user_abc123",
  "userNickname": "BIMO",
  "airlineCode": "KE",
  "airlineName": "대한항공",
  "route": "ICN-CDG",
  "imageUrl": "https://storage.googleapis.com/bimo-be.appspot.com/reviews/review_xyz/image.jpg",
  "ratings": {
    "seatComfort": 5,
    "inflightMeal": 4,
    "service": 3,
    "cleanliness": 3,
    "checkIn": 4
  },
  "overallRating": 3.8,
  "text": "좌석은 편했지만 기내식이 아쉬웠어요.",
  "isVerified": true,
  "createdAt": "2025-12-25T20:00:00Z"
}
```

---

### 3. airlines
항공사의 집계된 리뷰 통계를 저장하는 컬렉션입니다.

**경로**: `airlines/{airlineCode}`

**필드**:
- `airlineName`: (String) 항공사 이름 (예: "대한항공")
- `totalReviews`: (Number) 총 리뷰 개수
- `totalRatingSums`: (Map) 각 카테고리별 평점 총합
  ```json
  {
    "seatComfort": 5250,
    "inflightMeal": 4800,
    "service": 5500,
    "cleanliness": 5100,
    "checkIn": 4900
  }
  ```
- `averageRatings`: (Map) 각 카테고리별 평균 평점
  ```json
  {
    "seatComfort": 4.2,
    "inflightMeal": 3.84,
    "service": 4.4,
    "cleanliness": 4.08,
    "checkIn": 3.92
  }
  ```
  - 계산식: `averageRatings[category] = totalRatingSums[category] / totalReviews`
  - 소수점 2자리로 반올림
- `ratingBreakdown`: (Map) 각 카테고리별 점수 분포
  ```json
  {
    "seatComfort": {
      "5": 800,  // 5점 개수
      "4": 300,  // 4점 개수
      "3": 100,  // 3점 개수
      "2": 30,   // 2점 개수
      "1": 20    // 1점 개수
    },
    "inflightMeal": {
      "5": 600,
      "4": 400,
      "3": 200,
      "2": 40,
      "1": 10
    },
    ...
  }
  ```

**인덱스**:
- `airlineCode` (문서 ID)
- `totalReviews` (내림차순)
- `averageRatings.seatComfort` (내림차순)

**업데이트 로직 (Cloud Function)**:
- **트리거**: `reviews/{reviewId}` 문서 생성/수정/삭제
- **트랜잭션 사용**: 데이터 일관성 보장

**Cloud Function 의사코드**:
```javascript
// Firebase Cloud Function
exports.onReviewCreated = functions.firestore
  .document('reviews/{reviewId}')
  .onCreate(async (snap, context) => {
    const review = snap.data();
    const airlineCode = review.airlineCode;
    const ratings = review.ratings;
    
    // 트랜잭션 시작
    await admin.firestore().runTransaction(async (transaction) => {
      // 1. airlines/{airlineCode} 문서 읽기
      const airlineRef = admin.firestore()
        .collection('airlines')
        .doc(airlineCode);
      const airlineDoc = await transaction.get(airlineRef);
      
      // 2. 기존 데이터 가져오기
      const currentData = airlineDoc.exists 
        ? airlineDoc.data() 
        : { totalReviews: 0, totalRatingSums: {}, ratingBreakdown: {} };
      
      // 3. 새로운 값 계산
      const newTotalReviews = currentData.totalReviews + 1;
      
      const categories = ['seatComfort', 'inflightMeal', 'service', 'cleanliness', 'checkIn'];
      const newTotalRatingSums = { ...currentData.totalRatingSums };
      const newRatingBreakdown = { ...currentData.ratingBreakdown };
      const newAverageRatings = {};
      
      categories.forEach(category => {
        // 총합 업데이트
        const rating = ratings[category];
        newTotalRatingSums[category] = (newTotalRatingSums[category] || 0) + rating;
        
        // 평균 계산
        newAverageRatings[category] = Math.round(
          (newTotalRatingSums[category] / newTotalReviews) * 100
        ) / 100;
        
        // 분포 업데이트
        if (!newRatingBreakdown[category]) {
          newRatingBreakdown[category] = { "5": 0, "4": 0, "3": 0, "2": 0, "1": 0 };
        }
        newRatingBreakdown[category][rating.toString()] = 
          (newRatingBreakdown[category][rating.toString()] || 0) + 1;
      });
      
      // 4. 문서 업데이트
      transaction.set(airlineRef, {
        airlineName: review.airlineName,
        totalReviews: newTotalReviews,
        totalRatingSums: newTotalRatingSums,
        averageRatings: newAverageRatings,
        ratingBreakdown: newRatingBreakdown
      }, { merge: true });
    });
  });
```

**예시**:
```json
{
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
    "seatComfort": {
      "5": 800,
      "4": 300,
      "3": 100,
      "2": 30,
      "1": 20
    },
    "inflightMeal": {
      "5": 600,
      "4": 400,
      "3": 200,
      "2": 40,
      "1": 10
    },
    "service": {
      "5": 850,
      "4": 280,
      "3": 90,
      "2": 25,
      "1": 5
    },
    "cleanliness": {
      "5": 750,
      "4": 350,
      "3": 120,
      "2": 25,
      "1": 5
    },
    "checkIn": {
      "5": 700,
      "4": 380,
      "3": 140,
      "2": 25,
      "1": 5
    }
  }
}
```

---

## 관계 (Relationships)

### 1. myFlights ↔ reviews
- **일대일 관계** (선택적)
- `myFlights.reviewId` → `reviews/{reviewId}`
- 한 비행 기록은 최대 1개의 리뷰를 가질 수 있음
- 리뷰는 비행 기록과 연결되지 않을 수 있음 (독립 리뷰)

### 2. reviews → airlines
- **다대일 관계**
- `reviews.airlineCode` → `airlines/{airlineCode}`
- 여러 리뷰가 하나의 항공사를 참조
- Cloud Function을 통해 집계 데이터 자동 업데이트

### 3. reviews → users
- **다대일 관계**
- `reviews.userId` → `users/{userId}`
- 여러 리뷰가 하나의 사용자를 참조
- `userNickname`은 denormalize되어 저장 (성능 최적화)

---

## 인덱싱 전략

### 복합 인덱스
1. **reviews 컬렉션**:
   - `airlineCode` + `createdAt` (내림차순) - 항공사별 최신 리뷰 조회
   - `airlineCode` + `overallRating` (내림차순) - 항공사별 높은 평점 리뷰 조회
   - `userId` + `createdAt` (내림차순) - 사용자별 리뷰 조회

2. **myFlights 서브컬렉션**:
   - `status` + `departureTime` (내림차순) - 상태별 최신 비행 조회
   - `airlineCode` + `departureTime` (내림차순) - 항공사별 비행 조회

---

## 데이터 일관성 보장

### 1. 트랜잭션 사용
- `airlines` 집계 데이터 업데이트 시 반드시 트랜잭션 사용
- 동시성 문제 방지

### 2. Denormalization
- `reviews.userNickname`: JOIN 없이 빠른 조회
- `reviews.airlineName`: 항공사 정보 즉시 표시

### 3. Cloud Function
- 리뷰 생성/수정/삭제 시 `airlines` 자동 업데이트
- 서버 사이드에서 처리하여 클라이언트 오류 방지

---

## 보안 규칙 (Firestore Security Rules)

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // myFlights: 사용자는 자신의 비행 기록만 읽기/쓰기 가능
    match /users/{userId}/myFlights/{flightId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    
    // reviews: 모든 사용자가 읽기 가능, 인증된 사용자만 작성 가능
    match /reviews/{reviewId} {
      allow read: if true;
      allow create: if request.auth != null && request.auth.uid == request.resource.data.userId;
      allow update, delete: if request.auth != null && request.auth.uid == resource.data.userId;
    }
    
    // airlines: 모든 사용자가 읽기 가능, 쓰기는 Cloud Function만 가능
    match /airlines/{airlineCode} {
      allow read: if true;
      allow write: if false; // Cloud Function만 업데이트
    }
  }
}
```

---

## 성능 최적화

### 1. 페이지네이션
- 리뷰 목록: `limit()` + `startAfter()` 사용
- 기본 페이지 크기: 10-20개

### 2. 캐싱
- `airlines` 데이터는 자주 변경되지 않으므로 캐싱 권장
- TTL: 5-10분

### 3. 배치 작업
- 대량 데이터 업데이트 시 배치 쓰기 사용
- Firestore 배치 제한: 500개 문서

---

## 마이그레이션 가이드

### 기존 데이터 마이그레이션
1. `airlines` 집계 데이터 초기화
2. 기존 `reviews` 데이터 기반으로 집계 재계산
3. Cloud Function 배포 후 테스트

