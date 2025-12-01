"""
인증 프로바이더 단위 테스트
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timezone, timedelta

from app.feature.auth.providers.base_provider import BaseAuthProvider
from app.feature.auth.providers.google_provider import GoogleAuthProvider
from app.feature.auth.providers.apple_provider import AppleAuthProvider
from app.feature.auth.providers.kakao_provider import KakaoAuthProvider
from app.core.exceptions.exceptions import (
    TokenExpiredError,
    InvalidTokenError,
    TokenVerificationError,
    InvalidTokenPayloadError,
    AuthInitError,
    DatabaseError,
)


class TestBaseAuthProvider:
    """BaseAuthProvider 테스트"""

    def test_generate_api_token(self):
        """API 토큰 생성 테스트"""
        uid = "test-user-123"
        token = BaseAuthProvider.generate_api_token(uid)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_normalize_datetime_fields(self):
        """datetime 필드 정규화 테스트"""
        user_data = {
            "uid": "test-user",
            "created_at": "2024-01-01T00:00:00Z",
            "last_login_at": "2024-01-02T00:00:00Z"
        }
        
        normalized = BaseAuthProvider._normalize_datetime_fields(user_data)
        
        assert isinstance(normalized["created_at"], datetime)
        assert isinstance(normalized["last_login_at"], datetime)

    @pytest.mark.asyncio
    async def test_save_or_update_user_new_user(self, mock_firebase_db, sample_user_data):
        """신규 사용자 생성 테스트"""
        # Firestore 문서 모킹
        mock_doc = Mock()
        mock_doc.exists = False
        mock_doc.to_dict.return_value = {}
        
        mock_ref = Mock()
        mock_ref.get = Mock(return_value=mock_doc)
        mock_ref.set = Mock()
        mock_ref.update = Mock()
        
        mock_collection = Mock()
        mock_collection.document.return_value = mock_ref
        
        with patch("app.feature.auth.providers.base_provider.user_collection", mock_collection):
            user = await BaseAuthProvider._save_or_update_user(
                uid="test-user-123",
                email="test@example.com",
                display_name="Test User",
                photo_url="https://example.com/photo.jpg",
                provider_id="google.com"
            )
            
            assert user.uid == "test-user-123"
            assert user.email == "test@example.com"
            assert user.display_name == "Test User"
            mock_ref.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_or_update_user_existing_user(self, mock_firebase_db):
        """기존 사용자 업데이트 테스트"""
        existing_data = {
            "uid": "test-user-123",
            "email": "test@example.com",
            "display_name": "Test User",
            "photo_url": "https://example.com/photo.jpg",
            "provider_id": "google.com",
            "created_at": datetime.now(timezone.utc),
            "last_login_at": datetime.now(timezone.utc) - timedelta(days=1)
        }
        
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = existing_data
        
        mock_ref = Mock()
        mock_ref.get = Mock(return_value=mock_doc)
        mock_ref.update = Mock()
        
        mock_collection = Mock()
        mock_collection.document.return_value = mock_ref
        
        with patch("app.feature.auth.providers.base_provider.user_collection", mock_collection):
            user = await BaseAuthProvider._save_or_update_user(
                uid="test-user-123",
                email="test@example.com",
                display_name="Test User",
                photo_url="https://example.com/photo.jpg",
                provider_id="google.com"
            )
            
            assert user.uid == "test-user-123"
            mock_ref.update.assert_called_once()


class TestFirebaseAuthProvider:
    """FirebaseAuthProvider 테스트"""

    @pytest.mark.asyncio
    async def test_verify_token_success(self, mock_firebase_auth, sample_firebase_token):
        """토큰 검증 성공"""
        mock_firebase_auth.verify_id_token = Mock(return_value=sample_firebase_token)
        
        with patch("app.feature.auth.providers.firebase_provider.auth_client", mock_firebase_auth):
            result = await GoogleAuthProvider.verify_token("valid-token")
            
            assert result == sample_firebase_token
            assert result["uid"] == "test-user-123"

    @pytest.mark.asyncio
    async def test_verify_token_expired(self, mock_firebase_auth):
        """만료된 토큰"""
        from firebase_admin.auth import ExpiredIdTokenError
        
        mock_firebase_auth.verify_id_token = Mock(side_effect=ExpiredIdTokenError("Token expired", cause=None))
        
        with patch("app.feature.auth.providers.firebase_provider.auth_client", mock_firebase_auth):
            with pytest.raises(TokenExpiredError):
                await GoogleAuthProvider.verify_token("expired-token")

    @pytest.mark.asyncio
    async def test_verify_token_invalid(self, mock_firebase_auth):
        """유효하지 않은 토큰"""
        from firebase_admin.auth import InvalidIdTokenError
        
        mock_firebase_auth.verify_id_token = Mock(side_effect=InvalidIdTokenError("Invalid token", cause=None))
        
        with patch("app.feature.auth.providers.firebase_provider.auth_client", mock_firebase_auth):
            with pytest.raises(InvalidTokenError):
                await GoogleAuthProvider.verify_token("invalid-token")

    @pytest.mark.asyncio
    async def test_verify_token_auth_not_initialized(self):
        """Firebase Auth가 초기화되지 않은 경우"""
        with patch("app.feature.auth.providers.firebase_provider.auth_client", None):
            with pytest.raises(AuthInitError):
                await GoogleAuthProvider.verify_token("token")

    @pytest.mark.asyncio
    async def test_get_or_create_user_success(self, sample_firebase_token):
        """사용자 조회/생성 성공"""
        with patch.object(GoogleAuthProvider, "_save_or_update_user", new_callable=AsyncMock) as mock_save:
            from app.shared.schemas import UserInDB
            mock_user = UserInDB(
                uid="test-user-123",
                email="test@example.com",
                display_name="Test User",
                photo_url="https://example.com/photo.jpg",
                provider_id="google.com",
                created_at=datetime.now(timezone.utc),
                last_login_at=datetime.now(timezone.utc)
            )
            mock_save.return_value = mock_user
            
            user = await GoogleAuthProvider.get_or_create_user(sample_firebase_token, "Google")
            
            assert user.uid == "test-user-123"
            mock_save.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_or_create_user_missing_uid(self):
        """uid가 없는 토큰"""
        token_without_uid = {"email": "test@example.com"}
        
        with pytest.raises(InvalidTokenPayloadError):
            await GoogleAuthProvider.get_or_create_user(token_without_uid, "Google")


class TestGoogleAuthProvider:
    """GoogleAuthProvider 테스트"""

    @pytest.mark.asyncio
    async def test_authenticate_success(self, sample_firebase_token):
        """Google 로그인 성공"""
        with patch.object(GoogleAuthProvider, "verify_token", new_callable=AsyncMock) as mock_verify, \
             patch.object(GoogleAuthProvider, "get_or_create_user", new_callable=AsyncMock) as mock_get_user:
            
            from app.shared.schemas import UserInDB
            mock_user = UserInDB(
                uid="test-user-123",
                email="test@example.com",
                display_name="Test User",
                photo_url="https://example.com/photo.jpg",
                provider_id="google.com",
                created_at=datetime.now(timezone.utc),
                last_login_at=datetime.now(timezone.utc)
            )
            
            mock_verify.return_value = sample_firebase_token
            mock_get_user.return_value = mock_user
            
            result = await GoogleAuthProvider.authenticate("valid-token")
            
            assert "access_token" in result
            assert result["token_type"] == "bearer"
            assert result["user"] == mock_user
            assert isinstance(result["access_token"], str)


class TestAppleAuthProvider:
    """AppleAuthProvider 테스트"""

    @pytest.mark.asyncio
    async def test_authenticate_success(self, sample_firebase_token):
        """Apple 로그인 성공"""
        with patch.object(AppleAuthProvider, "verify_token", new_callable=AsyncMock) as mock_verify, \
             patch.object(AppleAuthProvider, "get_or_create_user", new_callable=AsyncMock) as mock_get_user:
            
            from app.shared.schemas import UserInDB
            mock_user = UserInDB(
                uid="test-user-123",
                email="test@example.com",
                display_name="Test User",
                photo_url="https://example.com/photo.jpg",
                provider_id="apple.com",
                created_at=datetime.now(timezone.utc),
                last_login_at=datetime.now(timezone.utc)
            )
            
            mock_verify.return_value = sample_firebase_token
            mock_get_user.return_value = mock_user
            
            result = await AppleAuthProvider.authenticate("valid-token")
            
            assert "access_token" in result
            assert result["token_type"] == "bearer"
            assert result["user"] == mock_user


class TestKakaoAuthProvider:
    """KakaoAuthProvider 테스트"""

    @pytest.mark.asyncio
    async def test_verify_token_success(self, sample_kakao_user_data):
        """Kakao 토큰 검증 성공"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = sample_kakao_user_data
            
            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            
            result = await KakaoAuthProvider.verify_token("valid-kakao-token")
            
            assert result["id"] == 123456789
            assert result["kakao_account"]["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_verify_token_failure(self):
        """Kakao 토큰 검증 실패"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.raise_for_status = Mock(side_effect=Exception("Unauthorized"))
            
            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            
            with pytest.raises(Exception):
                await KakaoAuthProvider.verify_token("invalid-token")

