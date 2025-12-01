"""
BIMO 백엔드 서비스의 중앙 집중식 커스텀 예외 클래스를 정의합니다.

각 예외 클래스는 HTTP 응답에 필요한 상태 코드(status_code),
에러 코드(error_code), 그리고 메시지(message)를 속성으로 가집니다.

이 예외들은 FastAPI의 예외 처리 미들웨어(@app.exception_handler)를 통해
클라이언트에게 일관된 형식의 JSON 오류 응답을 반환하는 데 사용됩니다.
"""

from __future__ import annotations

from typing import Optional

__all__ = [
    # Base Exceptions
    "AppConfigError",
    "CustomException",
    # Authentication & Authorization
    "AuthError",
    "AuthInitError",
    "TokenError",
    "TokenExpiredError",
    "InvalidTokenError",
    "TokenVerificationError",
    "InvalidTokenPayloadError",
    "PermissionDeniedError",
    # User Profile
    "UserProfileError",
    "UserProfileNotFoundError",
    "UserProfileConflictError",
    # Data & Database
    "DatabaseError",
    "FlightRecordNotFoundError",
    "FlightRecordConflictError",
    "ReviewNotFoundError",
    "ReviewImageUploadError",
    "AirlineMetricsUpdateError",
    # External Services
    "ExternalApiError",
    # LLM
    "LLMError",
    "PromptBuilderError",
    "LLMGenerationError",
]


# ===========================================================================
# Base Exception Classes
# ===========================================================================


class AppConfigError(Exception):
    """애플리케이션 설정 과정에서 발생하는 치명적인 오류를 나타냅니다."""

    def __init__(self, message: str):
        """
        Args:
            message (str): 설정 오류에 대한 구체적인 설명입니다.
        """
        self.message = f"Application configuration error: {message}"
        super().__init__(self.message)


class CustomException(Exception):
    """
    애플리케이션의 비즈니스 로직에서 발생하는 모든 커스텀 예외의 기본 클래스입니다.
    """

    def __init__(
        self,
        *,
        status_code: int = 500,
        error_code: str = "INTERNAL_SERVER_ERROR",
        message: str = "An internal server error occurred.",
    ):
        """
        Args:
            status_code (int): HTTP 상태 코드.
            error_code (str): 클라이언트에게 전달될 고유한 에러 코드.
            message (str): 클라이언트에게 보여줄 오류 메시지.
        """
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        super().__init__(self.message)


# ===========================================================================
# Authentication & Authorization Exceptions
# ===========================================================================


class AuthError(CustomException):
    """인증 또는 권한 부여 과정에서 발생하는 오류의 기본 클래스입니다."""

    def __init__(
        self,
        *,
        status_code: int = 401,
        error_code: str = "AUTH_ERROR",
        message: str = "Authentication or authorization error.",
    ):
        super().__init__(status_code=status_code, error_code=error_code, message=message)


class AuthInitError(AppConfigError):
    """Firebase Auth 등 인증 시스템 초기화에 실패했을 때 발생하는 오류입니다."""

    def __init__(self, message: str = "Authentication system initialization failed."):
        super().__init__(message)


class TokenError(AuthError):
    """JWT 토큰 처리와 관련된 오류의 기본 클래스입니다."""

    def __init__(
        self,
        *,
        status_code: int = 401,
        error_code: str = "TOKEN_ERROR",
        message: str = "An error occurred while processing the token.",
    ):
        super().__init__(status_code=status_code, error_code=error_code, message=message)


class TokenExpiredError(TokenError):
    """토큰이 만료되었을 때 발생하는 오류입니다."""

    def __init__(self, message: str = "The token has expired. Please log in again."):
        super().__init__(status_code=401, error_code="TOKEN_EXPIRED", message=message)


class InvalidTokenError(TokenError):
    """토큰의 형식이 유효하지 않거나 서명이 잘못되었을 때 발생하는 오류입니다."""

    def __init__(self, message: str = "The token is invalid. Please log in again."):
        super().__init__(status_code=401, error_code="INVALID_TOKEN", message=message)


class TokenVerificationError(TokenError):
    """토큰 검증 로직(예: Firebase)에서 오류가 발생했을 때 사용됩니다."""

    def __init__(self, message: str = "An error occurred during token verification."):
        super().__init__(
            status_code=401, error_code="TOKEN_VERIFICATION_FAILED", message=message
        )


class InvalidTokenPayloadError(TokenError):
    """토큰의 페이로드(내용)에 필수 정보가 누락되었을 때 발생하는 오류입니다."""

    def __init__(
        self, message: str = "The token payload is missing required user information."
    ):
        super().__init__(
            status_code=400, error_code="INVALID_TOKEN_PAYLOAD", message=message
        )


class PermissionDeniedError(AuthError):
    """사용자가 특정 리소스에 접근할 권한이 없을 때 발생하는 오류입니다."""

    def __init__(
        self, message: str = "You do not have permission to perform this action."
    ):
        super().__init__(status_code=403, error_code="PERMISSION_DENIED", message=message)


# ===========================================================================
# User Profile Exceptions
# ===========================================================================


class UserProfileError(CustomException):
    """사용자 프로필 관련 비즈니스 로직 오류의 기본 클래스입니다."""

    def __init__(
        self,
        *,
        status_code: int = 400,
        error_code: str = "USER_PROFILE_ERROR",
        message: str = "An error occurred related to the user profile.",
    ):
        super().__init__(status_code=status_code, error_code=error_code, message=message)


class UserProfileNotFoundError(UserProfileError):
    """특정 사용자 프로필을 찾을 수 없을 때 발생하는 오류입니다."""

    def __init__(self, user_id: Optional[str] = None):
        message = "User profile not found."
        if user_id:
            message += f" (userId={user_id})"
        super().__init__(status_code=404, error_code="USER_NOT_FOUND", message=message)


class UserProfileConflictError(UserProfileError):
    """사용자 프로필 생성 시 충돌(예: 이미 존재하는 사용자)이 발생했을 때 사용됩니다."""

    def __init__(self, user_id: Optional[str] = None):
        message = "A user with the given identifier already exists."
        if user_id:
            message += f" (userId={user_id})"
        super().__init__(
            status_code=409, error_code="USER_ALREADY_EXISTS", message=message
        )


# ===========================================================================
# Data & Database Exceptions
# ===========================================================================


class DatabaseError(CustomException):
    """데이터베이스 작업 중 일반적인 오류가 발생했을 때 사용됩니다."""

    def __init__(
        self,
        message: str = "A database error occurred.",
        status_code: int = 500,
        error_code: str = "DATABASE_ERROR",
    ):
        super().__init__(status_code=status_code, error_code=error_code, message=message)


class FlightRecordNotFoundError(DatabaseError):
    """특정 비행 기록을 찾을 수 없을 때 발생하는 오류입니다."""

    def __init__(self, flight_id: Optional[str] = None):
        message = "Flight record not found."
        if flight_id:
            message += f" (flightId={flight_id})"
        super().__init__(status_code=404, error_code="FLIGHT_NOT_FOUND", message=message)


class FlightRecordConflictError(DatabaseError):
    """비행 기록 생성 시 충돌이 발생했을 때 사용됩니다."""

    def __init__(self, flight_id: Optional[str] = None):
        message = "This flight record already exists."
        if flight_id:
            message += f" (flightId={flight_id})"
        super().__init__(
            status_code=409, error_code="FLIGHT_ALREADY_EXISTS", message=message
        )


class ReviewNotFoundError(DatabaseError):
    """특정 리뷰를 찾을 수 없을 때 발생하는 오류입니다."""

    def __init__(self, review_id: Optional[str] = None):
        message = "Review not found."
        if review_id:
            message += f" (reviewId={review_id})"
        super().__init__(status_code=404, error_code="REVIEW_NOT_FOUND", message=message)


class ReviewImageUploadError(DatabaseError):
    """리뷰 이미지 업로드에 실패했을 때 발생하는 오류입니다."""

    def __init__(self, message: str = "Failed to upload review image."):
        super().__init__(
            status_code=500, error_code="REVIEW_IMAGE_UPLOAD_FAILED", message=message
        )


class AirlineMetricsUpdateError(DatabaseError):
    """항공사 평점/리뷰 수 업데이트에 실패했을 때 발생하는 오류입니다."""

    def __init__(self, message: str = "Failed to update airline metrics."):
        super().__init__(
            status_code=500, error_code="AIRLINE_METRICS_UPDATE_FAILED", message=message
        )


# ===========================================================================
# External Service Exceptions
# ===========================================================================


class ExternalApiError(CustomException):
    """외부 API 연동 중 오류가 발생했을 때 사용됩니다."""

    def __init__(self, provider: str, detail: Optional[str] = None):
        """
        Args:
            provider (str): 오류가 발생한 외부 서비스의 이름 (e.g., "Amadeus").
            detail (Optional[str]): 외부 API가 반환한 구체적인 오류 메시지.
        """
        message = f"An error occurred with the {provider} API."
        if detail:
            message += f" Details: {detail}"
        super().__init__(
            status_code=502, error_code="EXTERNAL_API_FAILED", message=message
        )


# ===========================================================================
# LLM (Large Language Model) Exceptions
# ===========================================================================


class LLMError(CustomException):
    """LLM 관련 기능 수행 중 발생하는 오류의 기본 클래스입니다."""

    def __init__(
        self,
        *,
        status_code: int = 500,
        error_code: str = "LLM_ERROR",
        message: str = "An error occurred while interacting with the LLM.",
    ):
        super().__init__(status_code=status_code, error_code=error_code, message=message)


class PromptBuilderError(LLMError):
    """LLM에 전달할 프롬프트를 생성하는 데 실패했을 때 발생하는 오류입니다."""

    def __init__(self, message: str = "Failed to build the prompt for the AI model."):
        super().__init__(
            status_code=500, error_code="PROMPT_BUILDER_FAILED", message=message
        )


class LLMGenerationError(LLMError):
    """LLM이 유효한 응답을 생성하지 못했을 때 발생하는 오류입니다."""

    def __init__(
        self, message: str = "The AI model failed to generate a valid response."
    ):
        super().__init__(
            status_code=500, error_code="LLM_GENERATION_FAILED", message=message
        )