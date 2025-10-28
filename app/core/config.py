# app/core/config.py

import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수를 로드합니다.
# 이 함수는 .env 파일의 경로를 자동으로 찾습니다.
load_dotenv()

# .env 파일에 정의된 환경 변수를 읽어옵니다.
FIREBASE_KEY_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY")

# .env 파일에 정의된 SQL 환경 변수를 읽어옵니다,
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("환경 변수 'DATABASE_URL'이 설정되지 않았습니다.")