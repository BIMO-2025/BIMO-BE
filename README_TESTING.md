# 🧪 BIMO-BE 테스트 가이드

## 테스트 구조

```
tests/
├── conftest.py              # pytest 설정 및 공통 픽스처
├── unit/                    # 단위 테스트
│   ├── test_security.py    # 보안 모듈 테스트 (JWT)
│   ├── test_exceptions.py  # 예외 클래스 테스트
│   ├── test_wellness.py    # 시차적응 계산 함수 테스트
│   ├── test_wellness_service.py  # 시차적응 서비스 테스트
│   ├── test_auth_providers.py   # 인증 프로바이더 테스트
│   ├── test_auth_service.py     # 인증 서비스 테스트
│   ├── test_reviews.py     # 리뷰 서비스 테스트
│   └── test_llm.py         # LLM 서비스 테스트
└── integration/             # 통합 테스트
    ├── test_api_endpoints.py    # API 엔드포인트 테스트
    └── test_api_auth_flow.py    # 인증 플로우 통합 테스트
```

## 테스트 실행

### 모든 테스트 실행

```bash
# Windows
run_tests.bat

# macOS/Linux
chmod +x run_tests.sh
./run_tests.sh

# PowerShell
.\run_tests.ps1

# 또는 직접 실행
pytest
```

### 상세한 에러 정보와 함께 실행

테스트가 실패하면 다음 정보가 표시됩니다:
- **전체 스택 트레이스** (`--tb=long`)
- **로컬 변수 값** (`--showlocals`)
- **전체 추적 경로** (`--full-trace`)
- **요약 정보** (`-ra`: 모든 테스트 결과 요약)

```bash
pytest -v --tb=long --showlocals --full-trace -ra
```

### 특정 테스트만 실행

```bash
# 단위 테스트만
pytest tests/unit/

# 통합 테스트만
pytest tests/integration/

# 특정 파일만
pytest tests/unit/test_security.py

# 특정 테스트 함수만
pytest tests/unit/test_security.py::TestJWTToken::test_create_access_token

# 실패한 테스트만 재실행
pytest --lf
```

### 커버리지 포함 실행

```bash
pytest --cov=app --cov-report=html
```

커버리지 리포트는 `htmlcov/index.html`에서 확인할 수 있습니다.

## 테스트 마커

테스트는 마커로 분류되어 있습니다:

```bash
# 단위 테스트만
pytest -m unit

# 통합 테스트만
pytest -m integration

# 인증 관련 테스트만
pytest -m auth

# 느린 테스트 제외
pytest -m "not slow"
```

## 에러 정보 이해하기

테스트가 실패하면 다음과 같은 정보가 표시됩니다:

### 1. 스택 트레이스
- 어느 파일의 어느 줄에서 에러가 발생했는지
- 함수 호출 체인

### 2. 로컬 변수
- 에러 발생 시점의 모든 로컬 변수 값
- 함수 매개변수 값

### 3. Assertion 에러
- 예상값 vs 실제값 비교
- 어떤 조건이 실패했는지

### 예시

```
FAILED tests/unit/test_security.py::TestJWTToken::test_create_access_token
======================================== FAILURES ========================================
________________________________ test_create_access_token ________________________________

    def test_create_access_token(self):
        data = {"sub": "test-user-123"}
>       token = create_access_token(data=data)
E       AppConfigError: Application configuration error: JWT 설정이 필요합니다.

tests/unit/test_security.py:45: AppConfigError
----------------------------------- Locals -----------------------------------------------
self = <test_security.TestJWTToken object at 0x...>
data = {'sub': 'test-user-123'}
token = <not set>
```

## 테스트 작성 가이드

### 단위 테스트

- **목적**: 개별 함수/메서드의 동작 검증
- **원칙**: 외부 의존성(Firebase, Gemini API 등)은 모킹
- **예시**: `tests/unit/test_security.py`

### 통합 테스트

- **목적**: 여러 컴포넌트가 함께 작동하는지 검증
- **원칙**: 실제 API 엔드포인트를 호출하되, 외부 서비스는 모킹
- **예시**: `tests/integration/test_api_endpoints.py`

## 모킹 전략

### Firebase 모킹

```python
@pytest.fixture
def mock_firebase_db():
    with patch("app.core.firebase.db") as mock_db:
        yield mock_db
```

### Gemini API 모킹

```python
@pytest.fixture
def mock_gemini_client():
    with patch("app.feature.LLM.gemini_client.gemini_client") as mock_client:
        yield mock_client
```

## 테스트 커버리지 목표

- **최소 커버리지**: 70%
- **권장 커버리지**: 80% 이상
- **핵심 로직**: 90% 이상

## CI/CD 통합

GitHub Actions에서 자동으로 테스트를 실행하도록 설정할 수 있습니다:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements.txt
      - run: pytest --cov=app --cov-report=xml -v --tb=long
```

## 문제 해결

### 테스트가 실패하는 경우

1. **에러 메시지 확인**: 스택 트레이스와 로컬 변수 확인
2. **환경 변수 확인**: `.env` 파일이 올바르게 설정되었는지 확인
3. **의존성 확인**: `pip install -r requirements.txt` 실행
4. **모킹 확인**: 외부 서비스가 올바르게 모킹되었는지 확인

### 테스트가 느린 경우

- `pytest -m "not slow"`로 느린 테스트 제외
- 특정 테스트만 실행하여 디버깅

### 특정 테스트만 디버깅

```bash
# 특정 테스트만 실행하고 중단점 설정
pytest tests/unit/test_security.py::TestJWTToken::test_create_access_token -s

# pdb 디버거 사용
pytest --pdb tests/unit/test_security.py
```

## 추가 리소스

- [pytest 문서](https://docs.pytest.org/)
- [pytest-asyncio 문서](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov 문서](https://pytest-cov.readthedocs.io/)
