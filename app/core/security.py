from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

# .env 파일에서 설정을 가져오기 위해 import
from app.core.config import (
    API_SECRET_KEY,
    API_TOKEN_ALGORITHM,
    API_TOKEN_EXPIRE_MINUTES
)
# AppConfigError (시작 오류) 및 런타임 예외 임포트
from app.core.exceptions.exceptions import (
    AppConfigError,
    InvalidTokenError,
    TokenExpiredError,
)

# 비밀번호 해싱을 위한 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """일반 비밀번호와 해시된 비밀번호를 비교합니다."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """일반 비밀번호를 해시합니다."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    API Access Token (JWT)을 생성합니다.

    :param data: JWT payload에 포함될 데이터 (e.g., {"sub": user_uid})
    :param expires_delta: 토큰 만료 시간 (timedelta). None이면 .env의 기본값 사용.
    :return: 인코딩된 JWT (str)
    """
    to_encode = data.copy()

    # 토큰 만료 시간 설정
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # .env에서 설정한 기본 만료 시간을 사용
        expire = datetime.now(timezone.utc) + timedelta(minutes=API_TOKEN_EXPIRE_MINUTES)

    # 토큰 발급 시간(iat)과 만료 시간(exp)을 payload에 추가
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    })

    # .env 파일에 키가 설정되었는지 확인
    if not API_SECRET_KEY or not API_TOKEN_ALGORITHM:
        # AppConfigError를 발생시켜 앱 시작을 중단
        raise AppConfigError(
            "JWT 설정(API_SECRET_KEY, API_TOKEN_ALGORITHM)이 필요합니다. .env 파일을 확인하세요."
        )

    # JWT 토큰 인코딩
    encoded_jwt = jwt.encode(to_encode, API_SECRET_KEY, algorithm=API_TOKEN_ALGORITHM)

    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    API Access Token (JWT)을 디코딩하고 검증합니다.
    이 함수는 API 엔드포인트에서 사용자를 인증할 때 사용됩니다.

    :param token: 검증할 JWT
    :return: 디코딩된 payload (e.g., {"sub": user_uid, "exp": ..., "iat": ...})
    :raises TokenExpiredError: 토큰이 만료되었을 때
    :raises InvalidTokenError: 토큰이 유효하지 않을 때 (서명, 형식 오류 등)
    """
    # JWT 설정값 확인
    if not API_SECRET_KEY or not API_TOKEN_ALGORITHM:
        raise AppConfigError(
            "JWT 설정(API_SECRET_KEY, API_TOKEN_ALGORITHM)이 필요합니다. .env 파일을 확인하세요."
        )

    try:
        # JWT 디코딩 시도
        payload = jwt.decode(
            token,
            API_SECRET_KEY,
            algorithms=[API_TOKEN_ALGORITHM]
        )
        # payload에서 'sub' (사용자 ID) 값을 추출할 수 있습니다.
        # uid = payload.get("sub")
        return payload
    except jwt.ExpiredSignatureError:
        # 토큰 만료 시
        raise TokenExpiredError()
    except JWTError:
        # 그 외 모든 JWT 관련 에러 (서명 불일치, 형식 오류 등)
        raise InvalidTokenError()
    except Exception:
        # 예상치 못한 기타 오류
        raise InvalidTokenError(message="토큰 디코딩 중 알 수 없는 오류가 발생했습니다.")