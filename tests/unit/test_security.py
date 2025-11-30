"""
보안 모듈 단위 테스트
JWT 토큰 생성 및 검증 테스트
"""
import pytest
from datetime import timedelta
from jose import jwt

from app.core.security import (
    create_access_token,
    decode_access_token,
    verify_password,
    get_password_hash,
)
from app.core.exceptions.exceptions import (
    TokenExpiredError,
    InvalidTokenError,
    AppConfigError,
)


class TestPasswordHashing:
    """비밀번호 해싱 테스트"""

    def test_get_password_hash(self):
        """비밀번호 해싱 테스트"""
        password = "test-password-123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")  # bcrypt 해시 형식

    def test_verify_password_correct(self):
        """올바른 비밀번호 검증"""
        password = "test-password-123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """잘못된 비밀번호 검증"""
        password = "test-password-123"
        wrong_password = "wrong-password"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False


class TestJWTToken:
    """JWT 토큰 생성 및 검증 테스트"""

    def test_create_access_token(self):
        """JWT 토큰 생성 테스트"""
        data = {"sub": "test-user-123"}
        token = create_access_token(data=data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_custom_expiry(self):
        """커스텀 만료 시간으로 토큰 생성"""
        data = {"sub": "test-user-123"}
        expires_delta = timedelta(minutes=60)
        token = create_access_token(data=data, expires_delta=expires_delta)
        
        assert token is not None
        
        # 토큰 디코딩하여 exp 확인
        payload = decode_access_token(token)
        assert "exp" in payload
        assert "iat" in payload
        assert "sub" in payload
        assert payload["sub"] == "test-user-123"

    def test_decode_access_token_valid(self, sample_jwt_token):
        """유효한 토큰 디코딩"""
        payload = decode_access_token(sample_jwt_token)
        
        assert "sub" in payload
        assert "exp" in payload
        assert "iat" in payload
        assert payload["sub"] == "test-user-123"

    def test_decode_access_token_invalid(self):
        """유효하지 않은 토큰 디코딩"""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(InvalidTokenError):
            decode_access_token(invalid_token)

    def test_decode_access_token_expired(self):
        """만료된 토큰 디코딩"""
        # 과거 시간으로 만료된 토큰 생성
        from datetime import datetime, timezone
        from app.core.config import API_SECRET_KEY, API_TOKEN_ALGORITHM
        
        expired_data = {
            "sub": "test-user-123",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            "iat": datetime.now(timezone.utc) - timedelta(hours=2)
        }
        
        expired_token = jwt.encode(
            expired_data,
            API_SECRET_KEY,
            algorithm=API_TOKEN_ALGORITHM
        )
        
        with pytest.raises(TokenExpiredError):
            decode_access_token(expired_token)

    def test_token_contains_correct_data(self):
        """토큰에 올바른 데이터가 포함되어 있는지 확인"""
        data = {"sub": "test-user-123", "custom_field": "custom_value"}
        token = create_access_token(data=data)
        payload = decode_access_token(token)
        
        assert payload["sub"] == "test-user-123"
        assert payload["custom_field"] == "custom_value"
        assert "exp" in payload
        assert "iat" in payload

