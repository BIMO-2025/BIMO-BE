# Render 배포 가이드

## 🚨 중요 유의사항

### 1. CORS 설정 필수
**현재 코드에 CORS 미들웨어가 없습니다!** Appetize나 다른 외부 도메인에서 API를 호출하려면 반드시 추가해야 합니다.

#### 해결 방법
`app/main.py`에 CORS 미들웨어 추가:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://appetize.io",
        "https://*.appetize.io",
        "http://localhost:3000",  # 개발 환경
        # 프로덕션 도메인 추가
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. 환경 변수 설정

Render 대시보드에서 다음 환경 변수를 설정해야 합니다:

#### 필수 환경 변수
- `API_SECRET_KEY`: JWT 토큰 서명용 시크릿 키
- `FIREBASE_SERVICE_ACCOUNT_KEY`: **전체 JSON 문자열** (파일 경로가 아님!)
- `GEMINI_API_KEY`: Gemini API 키
- `DUFFEL_API_KEY`: Duffel API 키 (선택사항)
- `GOOGLE_IOS_CLIENT_ID`: Google OAuth iOS 클라이언트 ID (선택사항)

#### Firebase 서비스 계정 키 설정 방법
1. Firebase Console에서 서비스 계정 키 JSON 파일 다운로드
2. JSON 파일 전체 내용을 복사
3. Render 환경 변수 `FIREBASE_SERVICE_ACCOUNT_KEY`에 **전체 JSON 문자열**로 붙여넣기
   - 예: `{"type": "service_account", "project_id": "...", ...}`

⚠️ **주의**: 현재 코드는 파일 경로를 기대하지만, Render에서는 환경 변수로 직접 전달해야 합니다.

### 3. 포트 설정
Render는 `$PORT` 환경 변수를 제공합니다. `render.yaml`에서 이미 설정되어 있습니다.

### 4. 빌드 및 시작 명령어
- **빌드**: `pip install -r requirements.txt`
- **시작**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### 5. Python 버전
Render에서 Python 3.11 이상을 사용하도록 설정되어 있습니다.

### 6. 파일 시스템 제한
Render는 **읽기 전용 파일 시스템**을 사용합니다. 따라서:
- 파일 업로드는 메모리에서 처리 (현재 Base64 변환 방식은 문제 없음)
- 로컬 파일 저장 불가 (Firestore 사용 중이므로 문제 없음)

### 7. 네트워크 모니터링
현재 코드에 `NetworkMonitor`가 있는데, Render 환경에서는 불필요할 수 있습니다. 프로덕션에서는 비활성화하는 것을 고려하세요.

### 8. 로그 확인
Render 대시보드의 "Logs" 탭에서 실시간 로그를 확인할 수 있습니다.

## 📝 배포 체크리스트

- [ ] CORS 미들웨어 추가
- [ ] 환경 변수 모두 설정 (Render 대시보드)
- [ ] Firebase 서비스 계정 키를 JSON 문자열로 설정
- [ ] `render.yaml` 파일 커밋 및 푸시
- [ ] Render에서 GitHub 저장소 연결
- [ ] 첫 배포 후 로그 확인
- [ ] API 엔드포인트 테스트 (`/docs` 접속)

## 🔗 Appetize 연동 시 추가 고려사항

1. **CORS 설정**: Appetize 도메인을 `allow_origins`에 추가
2. **API 엔드포인트 URL**: Render 배포 URL을 Appetize 앱 설정에 입력
3. **HTTPS**: Render는 기본적으로 HTTPS를 제공하므로 문제 없음
4. **타임아웃**: Appetize에서 API 호출 시 타임아웃 설정 확인

## 🐛 문제 해결

### Firebase 초기화 실패
- 환경 변수 `FIREBASE_SERVICE_ACCOUNT_KEY`가 올바른 JSON 문자열인지 확인
- 로그에서 Firebase 초기화 오류 메시지 확인

### CORS 오류
- `app/main.py`에 CORS 미들웨어가 추가되었는지 확인
- Appetize 도메인이 `allow_origins`에 포함되어 있는지 확인

### 포트 바인딩 오류
- `--host 0.0.0.0` 설정 확인
- `$PORT` 환경 변수 사용 확인

