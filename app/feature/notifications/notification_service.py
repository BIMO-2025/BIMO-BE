import uuid
from datetime import datetime
from typing import List
from app.core.firebase import db
from app.feature.notifications.models import Notification, NotificationType

class NotificationService:
    def __init__(self):
        self.collection = db.collection("notifications")

    async def get_notifications(self, user_id: str) -> List[Notification]:
        docs = self.collection.where("user_id", "==", user_id)\
                              .order_by("created_at", direction="DESCENDING")\
                              .stream()
        return [Notification(**doc.to_dict()) for doc in docs]

    async def mark_as_read(self, notification_id: str) -> bool:
        doc_ref = self.collection.document(notification_id)
        doc = doc_ref.get()
        if doc.exists:
            doc_ref.update({"is_read": True})
            return True
        return False

    async def create_demo_notification(self, user_id: str):
        """테스트 및 시연용 알림 생성"""
        noti_id = str(uuid.uuid4())
        new_noti = Notification(
            id=noti_id,
            user_id=user_id,
            title="탑승 알림",
            body="KE081편 탑승이 시작되었습니다. 게이트 23으로 이동해주세요.",
            type=NotificationType.FLIGHT,
            is_read=False,
            created_at=datetime.utcnow().isoformat()
        )
        self.collection.document(noti_id).set(new_noti.dict())
