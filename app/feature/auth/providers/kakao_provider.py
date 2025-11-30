"""
Kakao 로그인 전용 인증 프로바이더
"""

import httpx
from fastapi.concurrency import run_in_threadpool
from firebase_admin import auth as firebase_auth
from firebase_admin.auth import UserRecord, UserNotFoundError

from app.core.firebase import auth_client
from app.shared.schemas import UserInDB
from app.feature.auth.providers.base_provider import BaseAuthProvider
from app.core.exceptions.exceptions import (
    AuthInitError,
    InvalidTokenPayloadError,
    DatabaseError,
    ExternalApiError,
    CustomException,
)


class KakaoAuthProvider(BaseAuthProvider):
    """Kakao 로그인을 처리하는 프로바이더"""

    KAKAO_USER_ME_URL = "https://kapi.kakao.com/v2/user/me"

    @staticmethod
    async def verify_token(token: str) -> dict:
        """
        [비동기 함수] Kakao Access Token을 검증하고 사용자 정보를 가져옵니다.
        
        Args:
            token: 클라이언트로부터 받은 Kakao Access Token
            
        Returns:
            Kakao API에서 반환된 사용자 정보
            
        Raises:
            ExternalApiError: Kakao API 요청 실패 또는 응답 오류
            InvalidTokenPayloadError: 토큰에서 필수 정보를 찾을 수 없을 때
        """
        headers = {"Authorization": f"Bearer {token}"}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(KakaoAuthProvider.KAKAO_USER_ME_URL, headers=headers)

            # Kakao API에서 에러가 반환된 경우
            if response.status_code != 200:
                raise ExternalApiError(
                    provider="Kakao",
                    message=f"Kakao API 오류: {response.status_code} {response.text}"
                )

            kakao_data = response.json()

            # 필수 정보(id, email) 확인
            if "id" not in kakao_data or "kakao_account" not in kakao_data:
                raise InvalidTokenPayloadError(message="Kakao 토큰에서 필수 정보를 찾을 수 없습니다.")

            kakao_account = kakao_data.get("kakao_account", {})
            if "email" not in kakao_account:
                raise InvalidTokenPayloadError(message="Kakao 계정에 이메일 정보가 없습니다.")

            return kakao_data

        except httpx.RequestError as e:
            raise ExternalApiError(
                provider="Kakao",
                message=f"Kakao API 요청 실패: {e}"
            )
        except Exception as e:
            if isinstance(e, CustomException):
                raise e
            raise ExternalApiError(
                provider="Kakao",
                message=f"Kakao 토큰 처리 중 오류: {e}"
            )

    @staticmethod
    def _find_user_by_email_sync(email: str) -> UserRecord:
        """[동기 함수] 이메일로 Firebase Auth 사용자를 찾습니다."""
        return firebase_auth.get_user_by_email(email)

    @staticmethod
    def _create_firebase_user_sync(email: str, display_name: str, photo_url: str) -> UserRecord:
        """[동기 함수] Firebase Auth에 새 사용자를 생성합니다."""
        return firebase_auth.create_user(
            email=email,
            display_name=display_name,
            photo_url=photo_url
        )

    @staticmethod
    async def get_or_create_firebase_user(kakao_data: dict) -> UserRecord:
        """
        [비동기 함수] Kakao 사용자 정보를 바탕으로 Firebase Auth 사용자를 조회하거나 생성합니다.
        
        Args:
            kakao_data: verify_token에서 반환된 Kakao 사용자 정보
            
        Returns:
            Firebase Auth UserRecord
            
        Raises:
            InvalidTokenPayloadError: Kakao 계정에 이메일 정보가 없을 때
            DatabaseError: Firebase Auth 사용자 생성/조회 실패
        """
        if not auth_client:
            raise AuthInitError()

        kakao_account = kakao_data.get("kakao_account", {})
        kakao_profile = kakao_account.get("profile", {})

        email = kakao_account.get("email")
        display_name = kakao_profile.get("nickname")
        photo_url = kakao_profile.get("profile_image_url")

        if not email:
            raise InvalidTokenPayloadError(message="Kakao 계정에 이메일 정보가 없습니다.")

        try:
            # 1. 이메일로 기존 Firebase Auth 사용자를 찾습니다.
            user_record = await run_in_threadpool(
                KakaoAuthProvider._find_user_by_email_sync, email
            )
            return user_record

        except UserNotFoundError:
            # 2. 사용자가 없으면 새로 생성합니다.
            try:
                user_record = await run_in_threadpool(
                    KakaoAuthProvider._create_firebase_user_sync,
                    email=email,
                    display_name=display_name,
                    photo_url=photo_url
                )
                return user_record
            except Exception as e:
                raise DatabaseError(message=f"Firebase Auth 사용자 생성 실패: {e}")

        except Exception as e:
            if isinstance(e, CustomException):
                raise e
            raise DatabaseError(message=f"Firebase Auth 사용자 조회 중 오류: {e}")

    @classmethod
    async def get_or_create_user(cls, firebase_user: UserRecord, fcm_token: str | None = None) -> UserInDB:
        """
        [비동기 함수] Firebase Auth 사용자 정보를 바탕으로 Firestore에서 사용자를 조회하거나 생성합니다.
        
        Args:
            firebase_user: Firebase Auth UserRecord
            fcm_token: FCM 토큰 (선택 사항)
            
        Returns:
            Firestore에 저장된 사용자 정보 (UserInDB)
            
        Raises:
            DatabaseError: Firestore 처리 중 오류 발생
        """
        return await cls._save_or_update_user(
            uid=firebase_user.uid,
            email=firebase_user.email,
            display_name=firebase_user.display_name,
            photo_url=firebase_user.photo_url,
            provider_id="kakao.com",
            fcm_token=fcm_token,
        )

    @classmethod
    async def authenticate(cls, token: str, fcm_token: str | None = None) -> dict:
        """
        [비동기 함수] Kakao 로그인 전체 프로세스를 처리합니다.
        
        Args:
            token: 클라이언트로부터 받은 Kakao Access Token
            
        Returns:
            {
                "access_token": "JWT 토큰",
                "token_type": "bearer",
                "user": UserInDB 객체
            }
        """
        # 1. Kakao 토큰 검증 및 사용자 정보 가져오기
        kakao_user_info = await cls.verify_token(token)

        # 2. Firebase Auth 사용자 조회 또는 생성
        firebase_user = await cls.get_or_create_firebase_user(kakao_user_info)

        # 3. Firestore 사용자 조회 또는 생성
        user = await cls.get_or_create_user(firebase_user, fcm_token=fcm_token)

        # 4. API 토큰 생성
        api_access_token = cls.generate_api_token(uid=user.uid)

        return {
            "access_token": api_access_token,
            "token_type": "bearer",
            "user": user
        }

