# 1. FastAPI 라이브러리를 가져옵니다.
from fastapi import FastAPI

# 2. FastAPI 앱(app) 객체를 생성합니다. (이게 우리 서버의 본체입니다)
app = FastAPI()

# 3. URL 접속 경로를 만듭니다.
# @app.get("/")는 "누군가 우리 서버의 '기본 주소'(/)로 접속하면" 이라는 뜻입니다.
@app.get("/")
def read_root():
    # 4. "Hello, BIMO!"라는 메시지를 JSON 형태로 반환(보여주기)합니다.
    return {"message": "Hello, BIMO!"}