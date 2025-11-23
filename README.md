# BIMO-BE

Backend API for BIMO — a personalized flight companion app that helps users plan, track, and recover from long flights.

## 🚀 빠른 시작

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일을 프로젝트 루트에 생성하고 다음 변수들을 설정하세요:

```env
# Firebase 설정
FIREBASE_SERVICE_ACCOUNT_KEY=./firebase_service_key.json

# JWT 토큰 설정
API_SECRET_KEY=your-secret-key-here
API_TOKEN_ALGORITHM=HS256
API_TOKEN_EXPIRE_MINUTES=30

# Gemini API 설정
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL_NAME=gemini-1.5-flash
```

자세한 내용은 [환경 변수 가이드](docs/API_AUTH_USER_SCHEMAS.md)를 참고하세요.

### 3. 서버 실행

#### 개발 모드 (자동 재시작)

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 프로덕션 모드

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. 서버 확인

서버가 실행되면 다음 URL에서 접근할 수 있습니다:

- **API 문서 (Swagger UI)**: http://localhost:8000/docs
- **API 문서 (ReDoc)**: http://localhost:8000/redoc
- **OpenAPI 스키마**: http://localhost:8000/openapi.json
- **루트 엔드포인트**: http://localhost:8000/

## 📚 API 엔드포인트

### 인증 (Authentication)
- `POST /auth/google/login` - Google 로그인
- `POST /auth/apple/login` - Apple 로그인
- `POST /auth/kakao/login` - Kakao 로그인

### 리뷰 (Reviews)
- `GET /reviews/airline/{airline_code}` - 항공사 리뷰 목록
- `GET /reviews/{review_id}` - 특정 리뷰 조회
- `POST /reviews/summarize` - LLM으로 리뷰 요약

### 시차적응 (Wellness)
- `POST /wellness/jetlag-plan` - 시차적응 계획 생성

### LLM
- `POST /llm/chat` - Gemini 채팅

### 알림 (Notifications)
- `POST /notifications/send` - 사용자에게 푸시 알림 전송
- `POST /notifications/token/update` - FCM 토큰 업데이트
- `POST /notifications/token/remove` - FCM 토큰 제거

## 🛠️ 개발 환경 설정

### Python 버전
- Python 3.10 이상 권장

### 가상 환경 사용 (권장)

```bash
# 가상 환경 생성
python -m venv venv

# 가상 환경 활성화
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

## 📖 문서

- [인증 및 사용자 API 스키마](docs/API_AUTH_USER_SCHEMAS.md)
- [테스트 가이드](README_TESTING.md)
- [FCM 알림 가이드](docs/FCM_NOTIFICATION_GUIDE.md)

## 🧪 테스트

### 테스트 실행

```bash
# 모든 테스트 실행
pytest

# 커버리지 포함
pytest --cov=app --cov-report=html

# 특정 테스트만
pytest tests/unit/
pytest tests/integration/
```

자세한 내용은 [테스트 가이드](README_TESTING.md)를 참고하세요.

## 🔧 문제 해결

### 포트가 이미 사용 중인 경우

다른 포트를 사용하세요:

```bash
uvicorn app.main:app --reload --port 8001
```

### Firebase 초기화 오류

`.env` 파일의 `FIREBASE_SERVICE_ACCOUNT_KEY` 경로가 올바른지 확인하세요.

### 모듈을 찾을 수 없는 경우

프로젝트 루트에서 실행하고 있는지 확인하세요:

```bash
# 올바른 위치
cd /path/to/BIMO-BE
uvicorn app.main:app --reload
```
