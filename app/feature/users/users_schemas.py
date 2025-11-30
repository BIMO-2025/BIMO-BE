from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, timezone

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
