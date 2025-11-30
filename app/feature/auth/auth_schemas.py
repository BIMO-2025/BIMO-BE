from pydantic import BaseModel, ConfigDict
from typing import Optional

# --- 요청 스키마 ---

class SocialLoginRequest(BaseModel):
    """
    클라이언트로부터 받을 소셜 로그인 ID Token
    Google, Apple, Kakao 모두 이 스키마를 사용할 수 있습니다.
    """
    token: str
    fcm_token: Optional[str] = None  # FCM 디바이스 토큰 (선택사항)

    model_config = ConfigDict(from_attributes=True)


# --- 응답 스키마 ---

class TokenResponse(BaseModel):
    """클라이언트에게 반환할 API Access Token"""
    access_token: str
    token_type: str = "bearer"

    model_config = ConfigDict(from_attributes=True)
