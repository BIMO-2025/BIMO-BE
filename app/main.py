# app/main.py

from fastapi import FastAPI

# 1. 기능별 라우터 import


# 2. Firebase 초기화 실행
# 이 import문은 app.core.firebase.py 코드를 실행시켜 SDK를 초기화합니다.
# 이 'db' 변수를 여기서 직접 사용할 필요는 없지만, import 자체로 의미가 있습니다.

from app.core import firebase


# 3. FastAPI 앱 인스턴스 생성
app = FastAPI(
    title="BIMO-BE Project",
    description="BIMO-BE FastAPI 서버입니다.",
    version="0.1.0",
)


# 4. 루트 엔드포인트 (서버 동작 확인용)
@app.get("/")
def read_root():
    return {"Hello": "Welcome to BIMO-BE API"}



# 5. 기능별 라우터 등록
app.include_router(auth_router.router)

# ... (다른 라우터들도 여기에 추가)