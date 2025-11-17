import os

from dotenv import load_dotenv

from app.core.exceptions.exceptions import AppConfigError

# .env 파일에서 환경 변수를 로드합니다.
load_dotenv()

# Firebase 설정
FIREBASE_KEY_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")

# API 자체 JWT 토큰 설정
API_SECRET_KEY = os.getenv("API_SECRET_KEY")
API_TOKEN_ALGORITHM = os.getenv("API_TOKEN_ALGORITHM", "HS256")

_expire_raw = os.getenv("API_TOKEN_EXPIRE_MINUTES")
try:
    # 설정값이 없으면 기본값 30분을 사용하고,
    # 값이 있으면 정수로 파싱합니다.
    API_TOKEN_EXPIRE_MINUTES = int(_expire_raw) if _expire_raw is not None else 30
except ValueError:
    # 잘못된 값이 들어온 경우, 명확한 설정 오류로 앱 시작을 중단합니다.
    raise AppConfigError(
        "환경 변수 'API_TOKEN_EXPIRE_MINUTES'는 정수여야 합니다. 예: 30"
    )

# LLM(Gemini) 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")