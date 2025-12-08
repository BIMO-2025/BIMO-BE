from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum

class LoginProvider(str, Enum):
    KAKAO = "kakao"
    GOOGLE = "google"
    APPLE = "apple"

class UserCreate(BaseModel):
    provider: LoginProvider
    provider_id: str
    email: Optional[str] = None
    nickname: Optional[str] = None # 없으면 랜덤 생성

class User(BaseModel):
    id: str  # UUID
    provider: str
    provider_id: str
    email: Optional[str]
    nickname: str
    profile_image: Optional[str] = None
    created_at: str
    
class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: User
