from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime

# --- 기본 모델 ---

class UserBase(BaseModel):
    """Firestore에 저장될 사용자 기본 정보"""
    uid: str
    email: Optional[EmailStr] = None
    display_name: Optional[str] = None
    photo_url: Optional[str] = None
    provider_id: str  # 예: "google.com", "apple.com"

    model_config = ConfigDict(from_attributes=True)


class UserInDB(UserBase):
    created_at: datetime
    last_login_at: datetime

    model_config = ConfigDict(from_attributes=True)