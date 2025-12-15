from pydantic import BaseModel, Field, ConfigDict, model_validator
from datetime import datetime, timezone
from app.feature.auth.auth_schemas import UserInfo

class UserSchema(BaseModel):
    """
    데이터베이스의 사용자 계정을 나타냅니다.
    경로: users/{userId}
    """
    nickname: str
    sleepPatternStart: datetime
    sleepPatternEnd: datetime
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "nickname": "BIMO",
                "sleepPatternStart": "2025-11-20T23:00:00Z",
                "sleepPatternEnd": "2025-11-21T07:00:00Z",
            }
        }
    )


# --- 닉네임 업데이트 관련 스키마 ---

class UpdateNicknameRequest(BaseModel):
    """닉네임 업데이트 요청 스키마"""
    nickname: str = Field(..., min_length=1, max_length=50, description="설정할 닉네임 (1-50자)")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "nickname": "새로운닉네임"
            }
        }
    )


class UpdateNicknameResponse(BaseModel):
    """닉네임 업데이트 응답 스키마"""
    success: bool
    message: str
    user: UserInfo

    model_config = ConfigDict(from_attributes=True)


# --- 수면 패턴 업데이트 관련 스키마 ---

class UpdateSleepPatternRequest(BaseModel):
    """수면 패턴 업데이트 요청 스키마"""
    userId: str = Field(..., description="사용자 ID")
    sleepPatternStart: str = Field(
        ..., 
        description="수면 시작 시간 (HH:MM 형식)",
        pattern=r"^([0-1][0-9]|2[0-3]):[0-5][0-9]$"
    )
    sleepPatternEnd: str = Field(
        ..., 
        description="수면 종료 시간 (HH:MM 형식)",
        pattern=r"^([0-1][0-9]|2[0-3]):[0-5][0-9]$"
    )
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "userId": "kMnkTjxuKRy8QWjBzt8xRk6kGG2",
                "sleepPatternStart": "23:00",
                "sleepPatternEnd": "07:00"
            }
        }
    )


class UpdateSleepPatternResponse(BaseModel):
    """수면 패턴 업데이트 응답 스키마"""
    success: bool
    message: str
    sleepPatternStart: str = Field(..., description="업데이트된 수면 시작 시간")
    sleepPatternEnd: str = Field(..., description="업데이트된 수면 종료 시간")
    
    model_config = ConfigDict(from_attributes=True)


# --- 프로필 사진 업데이트 관련 스키마 ---

class UpdateProfilePhotoRequest(BaseModel):
    """프로필 사진 업데이트 요청 스키마"""
    userId: str = Field(..., description="사용자 ID")
    photo_url: str = Field(..., description="프로필 사진 URL")
    # 하위 호환성(deprecated): 일부 클라이언트가 camelCase로 보낼 수 있음
    photoUrl: str | None = Field(
        default=None,
        description="(deprecated) 프로필 사진 URL (camelCase). 대신 photo_url을 사용하세요.",
        exclude=True,
    )
    photoURL: str | None = Field(
        default=None,
        description="(deprecated) 프로필 사진 URL (camelCase). 대신 photo_url을 사용하세요.",
        exclude=True,
    )

    @model_validator(mode="before")
    @classmethod
    def _normalize_photo_url(cls, data):
        if not isinstance(data, dict):
            return data

        def _clean(v):
            return v.strip() if isinstance(v, str) and v.strip() else None

        # 우선순위: photo_url > photoUrl > photoURL
        photo_url = _clean(data.get("photo_url"))
        photo_url = photo_url or _clean(data.get("photoUrl")) or _clean(data.get("photoURL"))
        if photo_url is not None:
            data["photo_url"] = photo_url
        return data
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "userId": "kMnkTjxuKRy8QWjBzt8xRk6kGG2",
                "photo_url": "https://example.com/profile.jpg"
            }
        }
    )


class UpdateProfilePhotoResponse(BaseModel):
    """프로필 사진 업데이트 응답 스키마"""
    success: bool
    message: str
    user: UserInfo
    
    model_config = ConfigDict(from_attributes=True)
