from typing import Optional, List
from pydantic import BaseModel
from app.feature.auth.models import User

class SleepPattern(BaseModel):
    bed_time: str = "23:00"
    wake_time: str = "07:00"
    average_hours: int = 8

class UserProfile(User):
    sleep_pattern: Optional[SleepPattern] = None

class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    sleep_pattern: Optional[SleepPattern] = None
