"""
인증 플로우 통합 테스트
전체 인증 프로세스를 테스트합니다.
"""
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone

from app.shared.schemas import UserInDB


class TestAuthFlow:
    """인증 플로우 통합 테스트"""

    @pytest.mark.asyncio
    async def test_google_auth_full_flow(self, client):
        """Google 로그인 전체 플로우"""
        # 1. Firebase 토큰 검증
        # 2. 사용자 조회/생성
        # 3. JWT 토큰 발급
        
        with patch("app.feature.auth.providers.google_provider.GoogleAuthProvider.authenticate", new_callable=AsyncMock) as mock_auth:
            mock_user = UserInDB(
                uid="test-user-123",
                email="test@example.com",
                display_name="Test User",
                photo_url="https://example.com/photo.jpg",
                provider_id="google.com",
                created_at=datetime.now(timezone.utc),
                last_login_at=datetime.now(timezone.utc)
            )
            
            mock_auth.return_value = {
                "access_token": "jwt-token-123",
                "token_type": "bearer",
                "user": mock_user
            }
            
            # 로그인 요청
            response = client.post(
                "/auth/google/login",
                json={"token": "firebase-id-token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # 응답 검증
            assert "access_token" in data
            assert data["token_type"] == "bearer"
            assert len(data["access_token"]) > 0
            
            # JWT 토큰 검증 (선택사항)
            from app.core.security import decode_access_token
            payload = decode_access_token(data["access_token"])
            assert payload["sub"] == "test-user-123"

    @pytest.mark.asyncio
    async def test_kakao_auth_full_flow(self, client):
        """Kakao 로그인 전체 플로우"""
        with patch("app.feature.auth.providers.kakao_provider.KakaoAuthProvider.authenticate", new_callable=AsyncMock) as mock_auth:
            mock_user = UserInDB(
                uid="kakao-user-123",
                email="kakao@example.com",
                display_name="Kakao User",
                photo_url="https://example.com/kakao.jpg",
                provider_id="kakao.com",
                created_at=datetime.now(timezone.utc),
                last_login_at=datetime.now(timezone.utc)
            )
            
            mock_auth.return_value = {
                "access_token": "jwt-token-kakao",
                "token_type": "bearer",
                "user": mock_user
            }
            
            response = client.post(
                "/auth/kakao/login",
                json={"token": "kakao-access-token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data

    @pytest.mark.asyncio
    async def test_auth_token_reuse(self, client):
        """발급받은 토큰 재사용 테스트"""
        # 1. 로그인하여 토큰 발급
        with patch("app.feature.auth.providers.google_provider.GoogleAuthProvider.authenticate", new_callable=AsyncMock) as mock_auth:
            mock_user = UserInDB(
                uid="test-user-123",
                email="test@example.com",
                display_name="Test User",
                photo_url="https://example.com/photo.jpg",
                provider_id="google.com",
                created_at=datetime.now(timezone.utc),
                last_login_at=datetime.now(timezone.utc)
            )
            
            mock_auth.return_value = {
                "access_token": "jwt-token-123",
                "token_type": "bearer",
                "user": mock_user
            }
            
            login_response = client.post(
                "/auth/google/login",
                json={"token": "firebase-id-token"}
            )
            
            assert login_response.status_code == 200
            token = login_response.json()["access_token"]
            
            # 2. 발급받은 토큰으로 API 호출 (향후 인증이 필요한 엔드포인트가 있으면 테스트)
            # 현재는 인증이 필요한 엔드포인트가 없으므로 토큰 검증만 수행
            from app.core.security import decode_access_token
            payload = decode_access_token(token)
            assert payload["sub"] == "test-user-123"

