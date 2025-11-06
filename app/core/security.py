from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

# .env 파일에서 설정을 가져오기 위해 import
from app.core.config import API_SECRET_KEY, API_TOKEN_ALGORITHM, API_TOKEN_EXPIRE_MINUTES

# 비밀번호 해싱을 위한 설정 (지금 당장 쓰진 않지만, 이메일/비번 로그인에 필요)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    우리 서비스 전용 API Access Token을 생성합니다.
    """
    to_encode = data.copy()

    # 토큰 만료 시간 설정
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # 설정 파일에서 가져온 기본 만료 시간 사용
        expire = datetime.now(timezone.utc) + timedelta(minutes=API_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    # .env 파일에 키가 설정되었는지 확인
    if not API_SECRET_KEY or not API_TOKEN_ALGORITHM:
        raise ValueError("JWT 설정(SECRET_KEY, ALGORITHM)이 필요합니다.")

    # JWT 토큰 인코딩
    encoded_jwt = jwt.encode(to_encode, API_SECRET_KEY, algorithm=API_TOKEN_ALGORITHM)
    return encoded_jwt


def verify_password(plain_password, hashed_password):
    """비밀번호 검증"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """비밀번호 해시 생성"""
    return pwd_context.hash(password)