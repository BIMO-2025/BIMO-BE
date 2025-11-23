"""
Firebase ID Token을 사용하는 인증 프로바이더의 기본 클래스
Google과 Apple이 상속받습니다.
"""

from abc import ABC
from fastapi.concurrency import run_in_threadpool
from firebase_admin import auth as firebase_auth

from app.core.firebase import auth_client
from app.shared.schemas import UserInDB
from app.feature.auth.providers.base_provider import BaseAuthProvider
from app.core.exceptions.exceptions import (
    AuthInitError,
    TokenExpiredError,
    InvalidTokenError,
    TokenVerificationError,
    InvalidTokenPayloadError,
    CustomException,
)


class FirebaseAuthProvider(BaseAuthProvider, ABC):
    """Firebase ID Token을 사용하는 인증 프로바이더의 기본 클래스"""

    @staticmethod
    def _verify_firebase_id_token_sync(token: str) -> dict:
        """
        [동기 함수] Firebase ID 토큰을 검증합니다.
        run_in_threadpool에서 실행될 함수입니다.
        """
        try:
            decoded_token = auth_client.verify_id_token(token)
            return decoded_token
        except firebase_auth.ExpiredIdTokenError:
            raise TokenExpiredError()
        except firebase_auth.InvalidIdTokenError:
            raise InvalidTokenError()
        except Exception as e:
            raise TokenVerificationError(message=f"Firebase 토큰 검증 중 오류 발생: {e}")

    @classmethod
    async def verify_token(cls, token: str) -> dict:
        """
        [비동기 함수] Firebase ID Token을 검증합니다.
        
        Args:
            token: 클라이언트로부터 받은 Firebase ID Token
            
        Returns:
            검증된 토큰의 디코딩된 정보 (uid, email, name, picture 등)
            
        Raises:
            AuthInitError: Firebase가 초기화되지 않았을 때
            TokenExpiredError: 토큰이 만료되었을 때
            InvalidTokenError: 토큰이 유효하지 않을 때
            TokenVerificationError: 토큰 검증 중 기타 오류
        """
        if not auth_client:
            raise AuthInitError()

        try:
            decoded_token = await run_in_threadpool(
                cls._verify_firebase_id_token_sync, token
            )
            return decoded_token
        except Exception as e:
            if isinstance(e, CustomException):
                raise e
            raise TokenVerificationError(message=f"Firebase 비동기 토큰 검증 중 오류: {e}")

    @classmethod
    async def get_or_create_user(cls, decoded_token: dict, provider_name: str) -> UserInDB:
        """
        [비동기 함수] 검증된 토큰 정보를 바탕으로 Firestore에서 사용자를 조회하거나 생성합니다.
        
        Args:
            decoded_token: verify_token에서 반환된 디코딩된 토큰 정보
            provider_name: 프로바이더 이름 (에러 메시지용, 예: "Google", "Apple")
            
        Returns:
            Firestore에 저장된 사용자 정보 (UserInDB)
            
        Raises:
            InvalidTokenPayloadError: 토큰에 필수 정보(uid)가 없을 때
            DatabaseError: Firestore 처리 중 오류 발생
        """
        uid = decoded_token.get("uid")
        email = decoded_token.get("email")
        display_name = decoded_token.get("name")
        photo_url = decoded_token.get("picture")
        provider_id = decoded_token.get("firebase", {}).get("sign_in_provider")

        if not uid:
            raise InvalidTokenPayloadError(message=f"{provider_name} 토큰에 uid가 없습니다.")

        if not provider_id:
            # provider_id가 없으면 기본값 설정 (하위 호환성)
            provider_id = f"{provider_name.lower()}.com"

        return await cls._save_or_update_user(
            uid=uid,
            email=email,
            display_name=display_name,
            photo_url=photo_url,
            provider_id=provider_id,
        )

