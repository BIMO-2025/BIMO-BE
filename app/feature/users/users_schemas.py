from pydantic import BaseModel, Field, ConfigDict
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
