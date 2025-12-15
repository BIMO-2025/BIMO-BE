# Base64 이미지 업로드 & API 개선사항

## 📅 작업 일자
**2025년 12월 16일**

---

## 🎯 작업 개요

이번 업데이트에서는 Base64 이미지 업로드 기능을 추가하고, 여러 API 개선 및 버그 수정을 진행했습니다.

---

## ✨ 주요 기능 추가

### 1. 📸 Base64 이미지 업로드 API

**엔드포인트:** `POST /uploads/images/base64`

#### 기능 설명
- 이미지 파일을 업로드하면 자동으로 압축 후 Base64 Data URL로 변환
- Firebase Storage 불필요 (완전 무료)
- Firestore에 직접 저장 가능

#### 기술 스펙
- **자동 압축:** 최대 800x800px, JPEG 품질 85%
- **형식 변환:** PNG/WebP/GIF → JPEG 자동 변환
- **크기 제한:** Base64 인코딩 후 최대 700KB
- **지원 형식:** JPG, PNG, WebP, GIF, BMP

#### 요청 예시
```bash
POST /uploads/images/base64
Content-Type: multipart/form-data

files: [이미지 파일 1]
files: [이미지 파일 2]
```

#### 응답 예시
```json
{
  "success": true,
  "images": [
    "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAA...",
    "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAA..."
  ],
  "count": 2,
  "message": "2개의 이미지가 성공적으로 처리되었습니다."
}
```

#### 사용 방법 (프론트엔드)
```javascript
// 1. 이미지 업로드
const formData = new FormData();
formData.append('files', imageFile);

const response = await fetch('/uploads/images/base64', {
  method: 'POST',
  body: formData
});

const { images } = await response.json();

// 2. 리뷰 작성 시 사용
await fetch('/reviews', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    ...reviewData,
    imageUrls: images  // Base64 문자열 배열
  })
});

// 3. 화면에 표시
<img src={images[0]} alt="리뷰 이미지" />
```

---

### 2. ❤️ 리뷰 좋아요 기능

**엔드포인트:** `POST /reviews/{review_id}/like`

#### 기능 설명
- 리뷰의 좋아요 수를 1 증가
- Authorization 헤더 불필요
- 실시간으로 Firestore 업데이트

#### 요청 예시
```bash
POST /reviews/abc123/like
```

#### 응답 예시
```json
{
  "review_id": "abc123",
  "likes": 15,
  "message": "좋아요가 추가되었습니다."
}
```

---

## 🔧 API 개선 사항

### 3. 🌏 수면패턴 한국 시간(KST) 적용

#### 변경 사항
- **이전:** UTC 시간으로 저장
- **현재:** 한국 시간(Asia/Seoul, UTC+9)으로 저장 및 조회

#### 영향받는 API
- `PUT /user/sleep-pattern` - 저장 시 KST 적용
- `GET /user/sleep-pattern` - 조회 시 KST 변환

#### 구현 내용
```python
import pytz

# 저장 시
kst = pytz.timezone('Asia/Seoul')
sleep_pattern_start = kst.localize(datetime(2025, 1, 1, 23, 0, 0))

# 조회 시
if sleep_start_dt.tzinfo is None:
    sleep_start_dt = pytz.utc.localize(sleep_start_dt).astimezone(kst)
else:
    sleep_start_dt = sleep_start_dt.astimezone(kst)
```

---

### 4. ✈️ 항공사 상세 API 스키마 수정

#### 문제
- 응답 모델이 `AirlineSchema`였지만 실제 반환은 `AirlineDetail`
- 필드명 불일치로 500 에러 발생

#### 해결
```python
# 수정 전
@router.get("/{airline_code}", response_model=AirlineSchema)

# 수정 후
@router.get("/{airline_code}", response_model=AirlineDetail)
```

---

## 🐛 버그 수정

### 5. 📝 리뷰 조회 Firestore 인덱스 에러 수정

#### 문제
- Firestore 복합 쿼리(필터링 + 정렬) 시 인덱스 필요
- 인덱스 미생성으로 500 에러 발생

#### 해결
- Firestore 쿼리에서 정렬 제거
- Python 메모리에서 정렬 수행

```python
# 수정 전 (인덱스 필요)
query = reviews_collection.where("userId", "==", user_id)
query = query.order_by("createdAt", direction="DESCENDING")

# 수정 후 (인덱스 불필요)
query = reviews_collection.where("userId", "==", user_id)
# Python에서 정렬
all_reviews.sort(key=lambda x: x.createdAt, reverse=True)
```

---

### 6. 🔐 리뷰 본인 인증 유지

**수정/삭제 API 본인 확인:**
- `PUT /reviews/{review_id}` - Bearer Token 필수
- `DELETE /reviews/{review_id}` - Bearer Token 필수
- JWT 토큰으로 사용자 ID 검증
- 본인의 리뷰만 수정/삭제 가능

---

## 📦 추가된 의존성

### Python 패키지
```bash
pip install Pillow
pip install python-multipart
```

#### 패키지 설명
- **Pillow (12.0.0):** 이미지 처리 및 압축
- **python-multipart (0.0.20):** 파일 업로드 지원

---

## 📁 파일 구조 변경

### 새로 추가된 파일
```
app/
├── feature/
│   └── uploads/
│       ├── __init__.py           # 새로 추가
│       └── upload_router.py      # 새로 추가
└── main.py                       # 라우터 등록 추가
```

### 수정된 파일
```
app/
├── feature/
│   ├── reviews/
│   │   ├── reviews_router.py     # 좋아요 엔드포인트 추가
│   │   └── reviews_service.py    # 좋아요 메서드 추가, 정렬 수정
│   ├── users/
│   │   └── user_service.py       # 수면패턴 KST 적용
│   └── airlines/
│       └── airline_router.py     # 응답 스키마 수정
└── main.py                       # upload_router 등록
```

---

## 🧪 테스트 결과

### Base64 이미지 업로드 테스트
```bash
✅ 응답 상태 코드: 200
✅ 성공: 1개의 이미지가 성공적으로 처리되었습니다.
✅ 이미지 개수: 1
✅ Base64 문자열 길이: 439 문자
✅ Base64 Data URL 형식 확인됨!
```

**테스트 스크립트:** `test_base64_upload.py`

---

## 📊 성능 최적화

### 이미지 압축 효과
| 원본 크기 | 압축 후 | Base64 후 | 절감률 |
|----------|---------|-----------|--------|
| 3MB      | ~80KB   | ~107KB    | 96.4%  |
| 1.5MB    | ~50KB   | ~67KB     | 95.5%  |
| 500KB    | ~30KB   | ~40KB     | 92.0%  |

### Firestore 읽기 최적화
- 복합 인덱스 불필요 → **비용 절감**
- Python 메모리 정렬 → **유연성 증가**

---

## 🚀 배포 가이드

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 환경 변수 확인
```bash
# .env 파일
FIREBASE_SERVICE_KEY_PATH=firebase_service_key.json
```

### 3. 서버 실행
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. API 문서 확인
```
http://localhost:8000/docs
```

---

## 📖 API 문서

### 전체 엔드포인트 목록

| 기능 | Method | Endpoint | 인증 |
|------|--------|----------|------|
| **이미지 업로드** | POST | `/uploads/images/base64` | ❌ |
| **리뷰 좋아요** | POST | `/reviews/{id}/like` | ❌ |
| 프로필 사진 변경 | PUT | `/user/profile/photo` | ❌ |
| 수면패턴 설정 | PUT | `/user/sleep-pattern` | ❌ |
| 수면패턴 조회 | GET | `/user/sleep-pattern` | ✅ |
| 내 리뷰 조회 | GET | `/reviews/users/{user_id}/reviews` | ❌ |
| 리뷰 작성 | POST | `/reviews` | ✅ |
| 리뷰 수정 | PUT | `/reviews/{id}` | ✅ |
| 리뷰 삭제 | DELETE | `/reviews/{id}` | ✅ |

---

## 🔍 추가 참고사항

### Firestore 문서 크기 제한
- **최대 크기:** 1MB
- **권장:** 리뷰당 이미지 3개 이하 (각 ~300KB)

### Base64 vs URL 비교

| 항목 | Base64 | URL (Storage) |
|------|--------|---------------|
| 비용 | 💰 무료 | 💸 유료 |
| 크기 | 📈 33% 증가 | 📊 원본 크기 |
| 관리 | ✅ 간단 | ⚙️ 복잡 |
| 성능 | 🐌 느림 | ⚡ 빠름 |

---

## 🎯 향후 계획

1. ⬜ 이미지 WebP 포맷 지원
2. ⬜ 이미지 리사이징 옵션 추가
3. ⬜ 좋아요 취소 기능 (DELETE)
4. ⬜ 좋아요 중복 방지 로직

---

## 👥 기여자

- **작업자:** KKS
- **작업 일자:** 2025-12-16
- **브랜치:** `feature/base64-image-upload-and-improvements`

---

## 📝 변경 이력

### v1.0.0 (2025-12-16)
- ✅ Base64 이미지 업로드 API 추가
- ✅ 리뷰 좋아요 기능 추가
- ✅ 수면패턴 한국 시간 적용
- ✅ 항공사 API 스키마 수정
- ✅ 리뷰 API Firestore 인덱스 에러 수정
- ✅ 의존성 패키지 추가 (Pillow, python-multipart)

---

## 📞 지원

문제가 발생하거나 질문이 있으시면 이슈를 등록해주세요.

**Swagger UI:** http://localhost:8000/docs
