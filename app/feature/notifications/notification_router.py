from typing import List
from fastapi import APIRouter, Depends, Header, HTTPException
from app.feature.notifications.notification_service import NotificationService
from app.feature.notifications.models import Notification

router = APIRouter(prefix="/notifications", tags=["notifications"])

def get_notification_service():
    return NotificationService()

async def get_current_user_id(authorization: str = Header(None)) -> str:
    if not authorization:
        return "demo_user_123"
    token = authorization.replace("Bearer ", "")
    return token.replace("demo_token_", "")

@router.get("", response_model=List[Notification])
async def get_notifications(
    user_id: str = Depends(get_current_user_id),
    service: NotificationService = Depends(get_notification_service)
):
    """알림 목록 조회"""
    # 데모: 목록이 비어있으면 하나 생성해줌
    notis = await service.get_notifications(user_id)
    if not notis:
        await service.create_demo_notification(user_id)
        notis = await service.get_notifications(user_id)
    return notis

@router.patch("/{notification_id}/read")
async def mark_as_read(
    notification_id: str,
    service: NotificationService = Depends(get_notification_service)
):
    """알림 읽음 처리"""
    success = await service.mark_as_read(notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"status": "success"}
