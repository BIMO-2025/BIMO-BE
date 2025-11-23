from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime

# --- 기본 모델 ---

class UserBase(BaseModel):
    """Firestore에 저장될 사용자 기본 정보"""
    uid: str
    email: Optional[EmailStr] = None
    display_name: Optional[str] = None
    photo_url: Optional[str] = None
    provider_id: str  # 예: "google.com", "apple.com"
    fcm_tokens: Optional[List[str]] = []  # FCM 디바이스 토큰 목록 (여러 디바이스 지원)

    model_config = ConfigDict(from_attributes=True)


class UserInDB(UserBase):
    created_at: datetime
    last_login_at: datetime

    model_config = ConfigDict(from_attributes=True)