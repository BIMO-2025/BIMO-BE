"""
인증 서비스 단위 테스트
"""
import pytest
from unittest.mock import AsyncMock, patch

from app.feature.auth import auth_service
from app.feature.auth.providers.google_provider import GoogleAuthProvider
from app.feature.auth.providers.apple_provider import AppleAuthProvider
from app.feature.auth.providers.kakao_provider import KakaoAuthProvider


class TestAuthService:
    """auth_service 모듈 테스트"""

    @pytest.mark.asyncio
    async def test_authenticate_with_google(self):
        """Google 로그인 서비스 테스트"""
        expected_result = {
            "access_token": "test-token",
            "token_type": "bearer",
            "user": {"uid": "test-user"}
        }
        
        with patch.object(GoogleAuthProvider, "authenticate", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = expected_result
            
            result = await auth_service.authenticate_with_google("firebase-token")
            
            assert result == expected_result
            mock_auth.assert_called_once_with("firebase-token", fcm_token=None)

    @pytest.mark.asyncio
    async def test_authenticate_with_apple(self):
        """Apple 로그인 서비스 테스트"""
        expected_result = {
            "access_token": "test-token",
            "token_type": "bearer",
            "user": {"uid": "test-user"}
        }
        
        with patch.object(AppleAuthProvider, "authenticate", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = expected_result
            
            result = await auth_service.authenticate_with_apple("firebase-token")
            
            assert result == expected_result
            mock_auth.assert_called_once_with("firebase-token", fcm_token=None)

    @pytest.mark.asyncio
    async def test_authenticate_with_kakao(self):
        """Kakao 로그인 서비스 테스트"""
        expected_result = {
            "access_token": "test-token",
            "token_type": "bearer",
            "user": {"uid": "test-user"}
        }
        
        with patch.object(KakaoAuthProvider, "authenticate", new_callable=AsyncMock) as mock_auth:
            mock_auth.return_value = expected_result
            
            result = await auth_service.authenticate_with_kakao("kakao-token")
            
            assert result == expected_result
            mock_auth.assert_called_once_with("kakao-token", fcm_token=None)

    def test_generate_api_token(self):
        """API 토큰 생성 테스트"""
        uid = "test-user-123"
        token = auth_service.generate_api_token(uid)
        
        assert token is not None
        assert isinstance(token, str)

