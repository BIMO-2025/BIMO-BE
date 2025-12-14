"""
예외 클래스 단위 테스트
"""
import pytest

from app.core.exceptions.exceptions import (
    CustomException,
    AuthError,
    TokenError,
    TokenExpiredError,
    InvalidTokenError,
    TokenVerificationError,
    InvalidTokenPayloadError,
    DatabaseError,
    ReviewNotFoundError,
    ExternalApiError,
    LLMError,
    AppConfigError,
)


class TestCustomException:
    """CustomException 테스트"""

    def test_custom_exception_default(self):
        """기본 CustomException 생성"""
        exc = CustomException()
        
        assert exc.status_code == 500
        assert exc.error_code == "INTERNAL_SERVER_ERROR"
        assert exc.message == "내부 서버 오류가 발생했습니다."

    def test_custom_exception_custom(self):
        """커스텀 CustomException 생성"""
        exc = CustomException(
            status_code=404,
            error_code="NOT_FOUND",
            message="Resource not found"
        )
        
        assert exc.status_code == 404
        assert exc.error_code == "NOT_FOUND"
        assert exc.message == "Resource not found"


class TestAuthExceptions:
    """인증 관련 예외 테스트"""

    def test_auth_error(self):
        """AuthError 기본값"""
        exc = AuthError()
        
        assert exc.status_code == 401
        assert exc.error_code == "AUTH_ERROR"

    def test_token_error(self):
        """TokenError 기본값"""
        exc = TokenError()
        
        assert exc.status_code == 401
        assert exc.error_code == "TOKEN_ERROR"

    def test_token_expired_error(self):
        """TokenExpiredError"""
        exc = TokenExpiredError()
        
        assert exc.status_code == 401
        assert exc.error_code == "TOKEN_EXPIRED"
        assert "만료" in exc.message

    def test_token_expired_error_custom_message(self):
        """커스텀 메시지가 있는 TokenExpiredError"""
        exc = TokenExpiredError("Custom expired message")
        
        assert exc.message == "Custom expired message"

    def test_invalid_token_error(self):
        """InvalidTokenError"""
        exc = InvalidTokenError()
        
        assert exc.status_code == 401
        assert exc.error_code == "INVALID_TOKEN"

    def test_token_verification_error(self):
        """TokenVerificationError"""
        exc = TokenVerificationError("Verification failed")
        
        assert exc.status_code == 401
        assert exc.error_code == "TOKEN_VERIFICATION_FAILED"
        assert exc.message == "Verification failed"

    def test_invalid_token_payload_error(self):
        """InvalidTokenPayloadError"""
        exc = InvalidTokenPayloadError("Missing uid")
        
        assert exc.status_code == 400
        assert exc.error_code == "INVALID_TOKEN_PAYLOAD"
        assert exc.message == "Missing uid"


class TestDatabaseExceptions:
    """데이터베이스 관련 예외 테스트"""

    def test_database_error(self):
        """DatabaseError"""
        exc = DatabaseError("Database connection failed")
        
        assert exc.status_code == 500
        assert exc.error_code == "DATABASE_ERROR"
        assert exc.message == "Database connection failed"

    def test_review_not_found_error(self):
        """ReviewNotFoundError"""
        exc = ReviewNotFoundError("review-123")
        
        assert exc.status_code == 404
        assert exc.error_code == "REVIEW_NOT_FOUND"
        assert "review-123" in exc.message


class TestOtherExceptions:
    """기타 예외 테스트"""

    def test_external_api_error(self):
        """ExternalApiError"""
        exc = ExternalApiError("Kakao", "API rate limit exceeded")
        
        assert exc.status_code == 502
        assert exc.error_code == "EXTERNAL_API_FAILED"
        assert "Kakao" in exc.message
        assert "API rate limit exceeded" in exc.message

    def test_llm_error(self):
        """LLMError"""
        exc = LLMError()
        
        assert exc.status_code == 500
        assert exc.error_code == "LLM_ERROR"

    def test_app_config_error(self):
        """AppConfigError"""
        exc = AppConfigError("Missing API key")
        
        assert "Application configuration error" in exc.message
        assert "Missing API key" in exc.message

