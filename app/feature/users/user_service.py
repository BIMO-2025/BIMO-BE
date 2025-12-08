from typing import Optional
from app.core.firebase import db
from app.feature.users.models import UserProfile, UserUpdate, SleepPattern

class UserService:
    def __init__(self):
        self.collection = db.collection("users")

    async def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        doc = self.collection.document(user_id).get()
        if not doc.exists:
            return None
        return UserProfile(**doc.to_dict())

    async def update_user(self, user_id: str, update_data: UserUpdate) -> UserProfile:
        doc_ref = self.collection.document(user_id)
        
        updates = {}
        if update_data.nickname:
            updates["nickname"] = update_data.nickname
        if update_data.sleep_pattern:
            # Pydantic -> Dict
            updates["sleep_pattern"] = update_data.sleep_pattern.dict()
            
        if updates:
            doc_ref.update(updates)
            
        updated_doc = doc_ref.get()
        return UserProfile(**updated_doc.to_dict())
