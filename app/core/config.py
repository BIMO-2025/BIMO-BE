# app/core/config.py

import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수를 로드합니다.
# 이 함수는 .env 파일의 경로를 자동으로 찾습니다.
load_dotenv()

# .env 파일에 정의된 환경 변수를 읽어옵니다.
# 1. Firebase Key
FIREBASE_KEY_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")
# 2. Postgresql URL
DATABASE_URL = os.getenv("DATABASE_URL")