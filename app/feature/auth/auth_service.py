from datetime import datetime, timezone
from fastapi import HTTPException, status
from fastapi.concurrency import run_in_threadpool
from firebase_admin.auth import InvalidIdTokenError, ExpiredIdTokenError

# app.core.firebase에서 db와 auth_client 가져오기
from app.core.firebase import db, auth_client
from app.core.security import create_access_token
from app.feature.auth.auth_schemas import UserBase, UserInDB

# 4. 새로 만든 커스텀 예외 임포트
from app.core.exceptions.exceptions import (
    TokenExpiredError,
    InvalidTokenError,
    FirebaseTokenError,
    FirebaseInitError,
    TokenUIDNotFoundError,
    DatabaseError, CustomException
)

# Firestore 'users' 컬렉션 참조
user_collection = db.collection("users")


def _verify_google_id_token_sync(token: str) -> dict:
    """
    [동기 함수] 실제 토큰을 검증하는 차단(blocking) I/O 작업.
    run_in_threadpool에서 실행될 함수입니다.
    """
    try:
        # 이 함수는 네트워크 통신을 하므로 동기/차단 방식입니다.
        decoded_token = auth_client.verify_id_token(token)
        return decoded_token
    except ExpiredIdTokenError:
        # HTTPException 대신 커스텀 예외 raise
        raise TokenExpiredError()
    except InvalidIdTokenError:
        # HTTPException 대신 커스텀 예외 raise
        raise InvalidTokenError()
    except Exception as e:
        # HTTPException 대신 커스텀 예외 raise
        raise FirebaseTokenError(detail=f"토큰 검증 중 오류 발생: {e}")


async def verify_google_id_token(token: str) -> dict:
    """
    [비동기 함수] Firebase Admin SDK를 사용하여 Google ID Token을 검증합니다.
    동기/차단 작업을 별도 스레드에서 실행합니다.
    """
    if not auth_client:
        # HTTPException 대신 커스텀 예외 raise
        raise FirebaseInitError()

    try:
        # 동기 함수(_verify_google_id_token_sync)를 스레드 풀에서 실행하고,
        # 그 결과를 비동기적으로 기다립니다.
        decoded_token = await run_in_threadpool(_verify_google_id_token_sync, token)
        return decoded_token
    except HTTPException as e:
        # 동기 함수에서 발생한 HTTPException을 그대로 다시 발생시킵니다.
        # (참고: _verify_google_id_token_sync가 HTTPException 대신 CustomException을
        # 발생시키므로, 이 블록은 CustomException을 잡도록 변경할 수도 있습니다.
        # 하지만 지금은 CustomException이 부모인 Exception에 의해 잡힐 것입니다.)
        raise e
    except Exception as e:
        # 스레드 풀 실행 중 예상치 못한 오류
        # 또는 _verify_google_id_token_sync에서 발생한 CustomException

        # e가 이미 CustomException인지 확인
        if isinstance(e, CustomException):
            raise e

        raise FirebaseTokenError(detail=f"비동기 토큰 검증 중 오류: {e}")


async def get_or_create_user(decoded_token: dict) -> UserInDB:
    """
    [비동기 함수] 검증된 토큰 정보를 바탕으로 Firestore에서 사용자를 조회하거나 생성합니다.
    모든 DB 작업을 별도 스레드에서 실행합니다.
    """
    uid = decoded_token.get("uid")
    email = decoded_token.get("email")
    display_name = decoded_token.get("name")
    photo_url = decoded_token.get("picture")
    provider_id = decoded_token.get("firebase", {}).get("sign_in_provider")

    if not uid:
        # HTTPException 대신 커스텀 예외 raise
        raise TokenUIDNotFoundError()

    try:
        user_ref = user_collection.document(uid)

        # user_ref.get()은 동기/차단 함수이므로 스레드 풀에서 실행합니다.
        user_doc = await run_in_threadpool(user_ref.get)

        current_time = datetime.now(timezone.utc).isoformat()

        if user_doc.exists:
            # 기존 사용자: 마지막 로그인 시간 업데이트
            user_data = user_doc.to_dict()
            user_data["last_login_at"] = current_time

            # user_ref.update()도 동기/차단 함수입니다.
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

            # user_ref.set()도 동기/차단 함수입니다.
            await run_in_threadpool(user_ref.set, user_in_db_data.model_dump())

            return user_in_db_data

    except Exception as e:
        # HTTPException 대신 커스텀 예외 raise
        # e가 이미 CustomException인지 확인
        if isinstance(e, CustomException):
            raise e

        raise DatabaseError(detail=f"데이터베이스 처리 중 오류 발생: {e}")


def generate_api_token(uid: str) -> str:
    """
    [동기 함수] 우리 서비스 전용 API Access Token (JWT)을 생성합니다.
    이 함수는 CPU 작업(암호화)이며, I/O 작업이 아니고 매우 빠르므로
    그냥 동기 함수로 두고 비동기 함수에서 바로 호출해도 괜찮습니다.
    (만약 이 작업이 매우 오래 걸린다면 이것도 run_in_threadpool 대상입니다.)
    """
    data = {"sub": uid}
    access_token = create_access_token(data=data)
    return access_token