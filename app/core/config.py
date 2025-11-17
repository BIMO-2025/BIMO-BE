import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수를 로드합니다.
load_dotenv()

# Firebase 설정
FIREBASE_KEY_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")

# API 자체 JWT 토큰 설정
API_SECRET_KEY = os.getenv("API_SECRET_KEY")
API_TOKEN_ALGORITHM = os.getenv("API_TOKEN_ALGORITHM", "HS256")
API_TOKEN_EXPIRE_MINUTES = int(os.getenv("API_TOKEN_EXPIRE_MINUTES", 30))