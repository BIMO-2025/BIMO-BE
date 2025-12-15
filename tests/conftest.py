"""
pytest 설정 및 공통 픽스처
"""
import os
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime, timezone
from dotenv import load_dotenv

# .env 파일 로드 (프로젝트 루트에서)
# 주의: setdefault보다 먼저 실행되어야 .env의 값이 우선됩니다
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path, override=False)  # override=False: 이미 설정된 환경 변수는 유지

# 테스트 환경 변수 설정 (기본값, .env에 없을 때만 사용)
os.environ.setdefault("API_SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("API_TOKEN_ALGORITHM", "HS256")
os.environ.setdefault("API_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("OLLAMA_BASE_URL", "http://localhost:11434")
os.environ.setdefault("OLLAMA_MODEL_NAME", "llama3.2:3b")
# FIREBASE_SERVICE_ACCOUNT_KEY는 .env에서 로드되거나, 없으면 기본값 사용
os.environ.setdefault("FIREBASE_SERVICE_ACCOUNT_KEY", "./firebase_service_key.json")

from app.main import app


@pytest.fixture
def client():
    """FastAPI 테스트 클라이언트"""
    return TestClient(app)


@pytest.fixture
def mock_firebase_db():
    """Firebase Firestore 모킹"""
    with patch("app.core.firebase.db") as mock_db:
        yield mock_db


@pytest.fixture
def mock_firebase_auth():
    """Firebase Auth 모킹"""
    with patch("app.core.firebase.auth_client") as mock_auth:
        yield mock_auth


@pytest.fixture
def mock_ollama_client():
    """Ollama 클라이언트 모킹"""
    with patch("app.feature.llm.ollama_client.get_ollama_client") as mock_client:
        yield mock_client


@pytest.fixture
def sample_user_data():
    """샘플 사용자 데이터"""
    return {
        "uid": "test-user-123",
        "email": "test@example.com",
        "display_name": "Test User",
        "photo_url": "https://example.com/photo.jpg",
        "provider_id": "google.com",
        "created_at": datetime.now(timezone.utc),
        "last_login_at": datetime.now(timezone.utc),
    }


@pytest.fixture
def sample_firebase_token():
    """샘플 Firebase ID Token 디코딩 결과"""
    return {
        "uid": "test-user-123",
        "email": "test@example.com",
        "name": "Test User",
        "picture": "https://example.com/photo.jpg",
        "firebase": {
            "sign_in_provider": "google.com"
        }
    }


@pytest.fixture
def sample_kakao_user_data():
    """샘플 Kakao 사용자 데이터"""
    return {
        "id": 123456789,
        "kakao_account": {
            "email": "test@example.com",
            "profile": {
                "nickname": "Test User",
                "profile_image_url": "https://example.com/photo.jpg"
            }
        }
    }


@pytest.fixture
def sample_review_data():
    """샘플 리뷰 데이터"""
    return {
        "id": "review-123",
        "userId": "user-123",
        "airlineCode": "KE",
        "airlineName": "대한항공",
        "flightNumber": "KE001",
        "text": "좋은 항공사입니다.",
        "overallRating": 4.5,
        "ratings": {
            "seatComfort": 4.0,
            "inflightMeal": 4.5,
            "service": 5.0,
            "cleanliness": 4.0,
            "checkIn": 4.5
        },
        "createdAt": datetime.now(timezone.utc).isoformat()
    }


@pytest.fixture
def sample_jwt_token():
    """샘플 JWT 토큰 생성"""
    from app.core.security import create_access_token
    return create_access_token(data={"sub": "test-user-123"})


@pytest.fixture(autouse=True)
def reset_environment():
    """각 테스트 전에 환경 변수 초기화"""
    yield
    # 테스트 후 정리 작업이 필요한 경우 여기에 작성

