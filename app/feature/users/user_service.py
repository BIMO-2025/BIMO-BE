"""
사용자 관련 서비스 모듈
"""

from datetime import datetime, timezone
from fastapi.concurrency import run_in_threadpool

from app.feature.auth.providers.base_provider import BaseAuthProvider
from app.core.firebase import db
from app.shared.schemas import UserInDB
from app.core.exceptions.exceptions import (
    DatabaseError,
    UserProfileNotFoundError,
    CustomException,
)

# Firestore 'users' 컬렉션 참조
user_collection = db.collection("users")


class UserService:
    """사용자 관련 비즈니스 로직을 처리하는 서비스"""

    @staticmethod
    async def update_display_name(uid: str, display_name: str) -> UserInDB:
        """
        사용자의 display_name(닉네임)을 업데이트합니다.
        
        Args:
            uid: 사용자 UID
            display_name: 새로운 닉네임
            
        Returns:
            업데이트된 사용자 정보 (UserInDB)
            
        Raises:
            UserProfileNotFoundError: 사용자를 찾을 수 없을 때
            DatabaseError: Firestore 업데이트 실패 시
        """
        # 1. Firestore에서 사용자 조회
        user_ref = user_collection.document(uid)
        user_doc = await run_in_threadpool(user_ref.get)
        
        if not user_doc.exists:
            raise UserProfileNotFoundError(user_id=uid)
        
        # 2. display_name 업데이트
        # 닉네임만 업데이트하므로 last_login_at은 변경하지 않음
        update_data = {
            "display_name": display_name.strip()
        }
        
        try:
            # Firestore 업데이트
            await run_in_threadpool(user_ref.update, update_data)
            
            # 3. 업데이트된 사용자 정보 조회 및 반환
            updated_doc = await run_in_threadpool(user_ref.get)
            user_data = updated_doc.to_dict()
            
            # 필수 필드 확인 및 기본값 설정
            if not user_data:
                raise DatabaseError(message="사용자 데이터를 가져올 수 없습니다.")
            
            # 필수 필드가 없으면 기본값 설정
            if "fcm_tokens" not in user_data:
                user_data["fcm_tokens"] = []
            
            # datetime 필드 정규화
            user_data = BaseAuthProvider._normalize_datetime_fields(user_data)
            
            return UserInDB(**user_data)
            
        except Exception as e:
            if isinstance(e, CustomException):
                raise e
            raise DatabaseError(message=f"닉네임 업데이트 실패: {e}")

