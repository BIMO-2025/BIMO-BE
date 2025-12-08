import uuid
from datetime import datetime
from typing import Optional
from app.core.firebase import db
from app.feature.auth.models import User, UserCreate, LoginProvider

class AuthService:
    def __init__(self):
        self.collection = db.collection("users")

    async def login_or_register(self, user_data: UserCreate) -> User:
        """
        소셜 로그인 후 회원가입 또는 로그인 처리
        provider + provider_id로 기존 유저 확인
        """
        # 1. 기존 유저 검색
        query = self.collection.where("provider", "==", user_data.provider.value)\
                               .where("provider_id", "==", user_data.provider_id)\
                               .limit(1).stream()
        
        existing_user_doc = next(query, None)
        
        if existing_user_doc:
            # 로그인
            data = existing_user_doc.to_dict()
            return User(**data)
        else:
            # 회원가입
            new_user = self._create_new_user(user_data)
            self.collection.document(new_user.id).set(new_user.dict())
            return new_user
            
    def _create_new_user(self, user_data: UserCreate) -> User:
        user_id = str(uuid.uuid4())
        nickname = user_data.nickname or f"Traveler_{user_id[:8]}"
        
        return User(
            id=user_id,
            provider=user_data.provider.value,
            provider_id=user_data.provider_id,
            email=user_data.email,
            nickname=nickname,
            created_at=datetime.utcnow().isoformat()
        )
        
    async def get_user(self, user_id: str) -> Optional[User]:
        doc = self.collection.document(user_id).get()
        if doc.exists:
            return User(**doc.to_dict())
        return None