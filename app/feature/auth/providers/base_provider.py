"""
인증 프로바이더의 추상 기본 클래스
모든 프로바이더가 공통으로 사용하는 메서드들을 정의합니다.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from fastapi.concurrency import run_in_threadpool

from app.core.security import create_access_token
from app.shared.schemas import UserBase, UserInDB
from app.core.exceptions.exceptions import (
    InvalidTokenPayloadError,
    DatabaseError,
    CustomException,
)

# Firestore 'users' 컬렉션 참조
from app.core.firebase import db

user_collection = db.collection("users")


class BaseAuthProvider(ABC):
    """모든 인증 프로바이더의 기본 클래스"""

    @staticmethod
    def generate_api_token(uid: str) -> str:
        """
        [동기 함수] 우리 서비스 전용 API Access Token (JWT)을 생성합니다.
        
        Args:
            uid: 사용자 고유 ID
            
        Returns:
            JWT 액세스 토큰 문자열
        """
        data = {"sub": uid}
        access_token = create_access_token(data=data)
        return access_token

    @staticmethod
    def _normalize_datetime_fields(user_data: dict) -> dict:
        """
        Firestore에서 읽은 datetime 필드를 datetime 객체로 변환합니다.
        
        Args:
            user_data: Firestore에서 읽은 사용자 데이터
            
        Returns:
            datetime 필드가 정규화된 사용자 데이터
        """
        if isinstance(user_data.get("created_at"), str):
            user_data["created_at"] = datetime.fromisoformat(
                user_data["created_at"].replace("Z", "+00:00")
            )
        if isinstance(user_data.get("last_login_at"), str):
            user_data["last_login_at"] = datetime.fromisoformat(
                user_data["last_login_at"].replace("Z", "+00:00")
            )
        return user_data

    @staticmethod
    async def _save_or_update_user(
        uid: str,
        email: str | None,
        display_name: str | None,
        photo_url: str | None,
        provider_id: str,
        fcm_token: str | None = None,
    ) -> UserInDB:
        """
        [비동기 함수] Firestore에서 사용자를 조회하거나 생성합니다.
        
        Args:
            uid: 사용자 고유 ID
            email: 사용자 이메일
            display_name: 사용자 표시 이름
            photo_url: 사용자 프로필 사진 URL
            provider_id: 인증 프로바이더 ID (예: "google.com", "apple.com", "kakao.com")
            
        Returns:
            Firestore에 저장된 사용자 정보 (UserInDB)
            
        Raises:
            DatabaseError: Firestore 처리 중 오류 발생
        """
        try:
            user_ref = user_collection.document(uid)
            user_doc = await run_in_threadpool(user_ref.get)

            current_time = datetime.now(timezone.utc)

            if user_doc.exists:
                # 기존 사용자: 마지막 로그인 시간 및 FCM 토큰 업데이트
                user_data = user_doc.to_dict()
                user_data["last_login_at"] = current_time
                
                # FCM 토큰 업데이트 (있을 경우)
                update_data = {"last_login_at": current_time}
                if fcm_token:
                    fcm_tokens = user_data.get("fcm_tokens", [])
                    if fcm_token not in fcm_tokens:
                        fcm_tokens.append(fcm_token)
                        update_data["fcm_tokens"] = fcm_tokens
                
                await run_in_threadpool(user_ref.update, update_data)
                
                # 업데이트된 데이터 반영
                if fcm_token and "fcm_tokens" in update_data:
                    user_data["fcm_tokens"] = update_data["fcm_tokens"]
                user_data["last_login_at"] = current_time

                # datetime 필드 정규화
                user_data = BaseAuthProvider._normalize_datetime_fields(user_data)

                return UserInDB(**user_data)
            else:
                # 신규 사용자: 사용자 정보 생성
                new_user_data = UserBase(
                    uid=uid,
                    email=email,
                    display_name=display_name,
                    photo_url=photo_url,
                    provider_id=provider_id
                )

                # FCM 토큰 포함하여 사용자 데이터 생성
                user_data_dict = new_user_data.model_dump()
                if fcm_token:
                    user_data_dict["fcm_tokens"] = [fcm_token]
                else:
                    user_data_dict["fcm_tokens"] = []
                
                user_in_db_data = UserInDB(
                    **user_data_dict,
                    created_at=current_time,
                    last_login_at=current_time
                )

                await run_in_threadpool(user_ref.set, user_in_db_data.model_dump())

                return user_in_db_data

        except Exception as e:
            if isinstance(e, CustomException):
                raise e
            raise DatabaseError(message=f"Firestore 사용자 처리 중 오류 발생: {e}")

    @abstractmethod
    async def authenticate(token: str) -> dict:
        """
        [비동기 함수] 로그인 전체 프로세스를 처리합니다.
        
        Args:
            token: 클라이언트로부터 받은 인증 토큰
            
        Returns:
            {
                "access_token": "JWT 토큰",
                "token_type": "bearer",
                "user": UserInDB 객체
            }
        """
        pass

