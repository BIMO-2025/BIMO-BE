from typing import Optional
from pydantic import BaseModel
from enum import Enum

class NotificationType(str, Enum):
    FLIGHT = "flight"
    REVIEW = "review"
    SYSTEM = "system"

class Notification(BaseModel):
    id: str
    user_id: str
    title: str
    body: str
    type: NotificationType
    is_read: bool
    created_at: str
    link_url: Optional[str] = None
