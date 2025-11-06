from pydantic import BaseModel, EmailStr
from typing import Optional

# --- 기본 모델 ---

class UserBase(BaseModel):
    """Firestore에 저장될 사용자 기본 정보"""
    uid: str
    email: Optional[EmailStr] = None
    display_name: Optional[str] = None
    photo_url: Optional[str] = None
    provider_id: str # 예: "google.com", "apple.com"

class UserInDB(UserBase):
    created_at: str
    last_login_at: str

# --- 요청 스키마 ---

class SocialLoginRequest(BaseModel):
    """
    클라이언트로부터 받을 소셜 로그인 ID Token
    Google, Apple, Kakao 모두 이 스키마를 사용할 수 있습니다.
    """
    token: str

# --- 응답 스키마 ---

class TokenResponse(BaseModel):
    """클라이언트에게 반환할 API Access Token"""
    access_token: str
    token_type: str = "bearer"