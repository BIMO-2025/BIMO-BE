"""
애플리케이션 설정 및 환경 변수 관리
"""

import os
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.exceptions.exceptions import AppConfigError


class Settings(BaseSettings):
    """애플리케이션 설정 클래스"""
    
    # Firebase 설정
    FIREBASE_SERVICE_ACCOUNT_KEY: Optional[str] = None

    # API 자체 JWT 토큰 설정
    API_SECRET_KEY: str
    API_TOKEN_ALGORITHM: str = "HS256"
    API_TOKEN_EXPIRE_MINUTES: int = 30

    # LLM(Gemini) 설정
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL_NAME: str = "gemini-1.5-flash"

    # Amadeus API 설정
    AMADEUS_API_KEY: Optional[str] = None
    AMADEUS_API_SECRET: Optional[str] = None
    AMADEUS_ENVIRONMENT: str = "test"

    # Google OAuth 설정 (iOS)
    GOOGLE_IOS_CLIENT_ID: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # 정의되지 않은 환경변수는 무시
    )


@lru_cache()
def get_settings() -> Settings:
    """
    설정 객체를 반환합니다.
    lru_cache로 싱글톤 패턴 구현
    
    Returns:
        Settings 인스턴스
    
    Raises:
        AppConfigError: 환경 변수 설정 오류 시
    """
    try:
        return Settings()
    except Exception as e:
        raise AppConfigError(f"환경 변수 설정 오류: {e}")


# 모듈 레벨 settings (하위 호환성)
try:
    settings = get_settings()
except AppConfigError:
    # 설정 오류 시 앱 시작 중단
    raise


__all__ = ["Settings", "get_settings", "settings"]
