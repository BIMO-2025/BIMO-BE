import httpx  # 카카오 API 호출을 위해 import
from datetime import datetime, timezone
from fastapi.concurrency import run_in_threadpool
from firebase_admin import auth as firebase_auth
from firebase_admin.auth import InvalidIdTokenError, ExpiredIdTokenError, UserRecord, UserNotFoundError

# app.core.firebase에서 db와 auth_client 가져오기
from app.core.firebase import db, auth_client
from app.core.security import create_access_token
from app.feature.auth.auth_schemas import UserBase, UserInDB

# 4. exceptions.py에 정의된 커스텀 예외 임포트 (이름 수정)
from app.core.exceptions.exceptions import (
    CustomException,
    TokenExpiredError,
    InvalidTokenError,
    TokenVerificationError,  # FirebaseTokenError -> TokenVerificationError
    AuthInitError,  # FirebaseInitError -> AuthInitError
    InvalidTokenPayloadError,  # TokenUIDNotFoundError -> InvalidTokenPayloadError
    DatabaseError,
    ExternalApiError
)

# Firestore 'users' 컬렉션 참조
user_collection = db.collection("users")


def _verify_firebase_id_token_sync(token: str) -> dict:
    """
    [동기 함수] 실제 Firebase ID 토큰을 검증하는 차단(blocking) I/O 작업.
    run_in_threadpool에서 실행될 함수입니다. (Google, Apple 공용)
    """
    try:
        # 이 함수는 네트워크 통신을 하므로 동기/차단 방식입니다.
        decoded_token = auth_client.verify_id_token(token)
        return decoded_token
    except ExpiredIdTokenError:
        raise TokenExpiredError()
    except InvalidIdTokenError:
        raise InvalidTokenError()
    except Exception as e:
        raise TokenVerificationError(message=f"토큰 검증 중 오류 발생: {e}")


async def verify_firebase_id_token(token: str) -> dict:
    """
    [비동기 함수] Firebase Admin SDK를 사용하여 ID Token을 검증합니다.
    (Google, Apple 공용)
    """
    if not auth_client:
        raise AuthInitError()

    try:
        decoded_token = await run_in_threadpool(_verify_firebase_id_token_sync, token)
        return decoded_token
    except Exception as e:
        if isinstance(e, CustomException):
            raise e
        raise TokenVerificationError(message=f"비동기 토큰 검증 중 오류: {e}")


# --- Kakao 로그인 전용 함수들 ---

async def verify_kakao_token(token: str) -> dict:
    """
    [비동기 함수] 클라이언트로부터 받은 Kakao Access Token을 검증하고,
    Kakao API에서 사용자 정보를 가져옵니다. (httpx 사용)
    """
    KAKAO_USER_ME_URL = "https://kapi.kakao.com/v2/user/me"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        # httpx.AsyncClient를 사용하여 비동기 HTTP 요청
        async with httpx.AsyncClient() as client:
            response = await client.get(KAKAO_USER_ME_URL, headers=headers)

        # Kakao API에서 에러가 반환된 경우
        if response.status_code != 200:
            raise ExternalApiError(
                message=f"Kakao API 오류: {response.status_code} {response.text}"
            )

        kakao_data = response.json()

        # 필수 정보(id, email) 확인
        if "id" not in kakao_data or "kakao_account" not in kakao_data or "email" not in kakao_data["kakao_account"]:
            raise InvalidTokenPayloadError(message="Kakao 토큰에서 필수 정보를 찾을 수 없습니다.")

        return kakao_data

    except httpx.RequestError as e:
        raise ExternalApiError(message=f"Kakao API 요청 실패: {e}")
    except Exception as e:
        if isinstance(e, CustomException):
            raise e
        raise ExternalApiError(message=f"Kakao 토큰 처리 중 오류: {e}")


def _find_user_by_email_sync(email: str) -> UserRecord:
    """[동기 함수] 이메일로 Firebase Auth 사용자를 찾습니다."""
    return firebase_auth.get_user_by_email(email)


def _create_firebase_user_sync(email: str, display_name: str, photo_url: str) -> UserRecord:
    """[동기 함수] Firebase Auth에 새 사용자를 생성합니다."""
    return firebase_auth.create_user(
        email=email,
        display_name=display_name,
        photo_url=photo_url
    )


async def get_or_create_firebase_user(kakao_data: dict) -> UserRecord:
    """
    [비동기 함수] Kakao 사용자 정보를 바탕으로
    Firebase Auth의 사용자를 조회하거나 생성합니다.
    """
    kakao_account = kakao_data.get("kakao_account", {})
    kakao_profile = kakao_account.get("profile", {})

    email = kakao_account.get("email")
    display_name = kakao_profile.get("nickname")
    photo_url = kakao_profile.get("profile_image_url")

    if not email:
        raise InvalidTokenPayloadError(message="Kakao 계정에 이메일 정보가 없습니다.")

    try:
        # 1. 이메일로 기존 Firebase Auth 사용자를 찾습니다. (동기 -> 스레드 풀)
        user_record = await run_in_threadpool(_find_user_by_email_sync, email)
        return user_record

    except UserNotFoundError:
        # 2. 사용자가 없으면 새로 생성합니다. (동기 -> 스레드 풀)
        try:
            user_record = await run_in_threadpool(
                _create_firebase_user_sync,
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


# --- Firestore DB 공용 함수 ---

async def get_or_create_user(decoded_token: dict) -> UserInDB:
    """
    [비동기 함수] 검증된 토큰 정보를 바탕으로 Firestore에서 사용자를 조회하거나 생성합니다.
    (Google, Apple, Kakao 공용)
    """
    uid = decoded_token.get("uid")
    email = decoded_token.get("email")
    display_name = decoded_token.get("name")
    photo_url = decoded_token.get("picture")
    # kakao의 경우 우리가 "kakao.com"을 직접 넣어줍니다.
    provider_id = decoded_token.get("firebase", {}).get("sign_in_provider")

    if not uid:
        raise InvalidTokenPayloadError()  # 커스텀 예외 사용

    try:
        user_ref = user_collection.document(uid)

        # user_ref.get()은 동기/차단 함수이므로 스레드 풀에서 실행합니다.
        user_doc = await run_in_threadpool(user_ref.get)

        current_time = datetime.now(timezone.utc).isoformat()

        if user_doc.exists:
            # 기존 사용자: 마지막 로그인 시간 업데이트
            user_data = user_doc.to_dict()
            user_data["last_login_at"] = current_time

            await run_in_threadpool(user_ref.update, {"last_login_at": current_time})

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

            user_in_db_data = UserInDB(
                **new_user_data.model_dump(),
                created_at=current_time,
                last_login_at=current_time
            )

            await run_in_threadpool(user_ref.set, user_in_db_data.model_dump())

            return user_in_db_data

    except Exception as e:
        if isinstance(e, CustomException):
            raise e
        raise DatabaseError(message=f"Firestore 처리 중 오류 발생: {e}")


def generate_api_token(uid: str) -> str:
    """
    [동기 함수] 우리 서비스 전용 API Access Token (JWT)을 생성합니다.
    (CPU 작업이므로 async가 필요 없습니다.)
    """
    data = {"sub": uid}
    access_token = create_access_token(data=data)
    return access_token