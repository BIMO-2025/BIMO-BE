"""
알림 관련 스키마
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict


class SendNotificationRequest(BaseModel):
    """알림 전송 요청"""
    title: str
    body: str
    data: Optional[Dict[str, str]] = None
    image_url: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class UpdateFCMTokenRequest(BaseModel):
    """FCM 토큰 업데이트 요청"""
    fcm_token: str
    
    model_config = ConfigDict(from_attributes=True)


class NotificationResponse(BaseModel):
    """알림 전송 응답"""
    success_count: int
    failure_count: int
    message: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

