# app/main.py (수정)

from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List

# 1. Firebase 및 설정 import (기존 코드)
from app.core import firebase
from app.core.config import DATABASE_URL  # (확인용)

# 2. DB 관련 모듈 import (새로 추가)
from app.core.database import get_session, create_db_and_tables
from app.models.item_model import Item, ItemCreate, ItemRead


# 3. Lifespan 이벤트 핸들러 (새로 추가)
# FastAPI 서버가 시작/종료될 때 실행할 로직
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("--- 서버 시작 ---")
    print(f"DB URL: {DATABASE_URL}")  # .env에서 잘 읽어왔는지 확인
    await create_db_and_tables()
    print("DB 테이블 생성 완료")

    yield  # 이 시점에서 FastAPI 앱이 실행됨

    print("--- 서버 종료 ---")


# 4. FastAPI 앱 인스턴스 생성 (lifespan 추가)
app = FastAPI(
    title="BIMO-BE Project",
    description="BIMO-BE FastAPI 서버입니다. (PostgreSQL 연동)",
    version="0.1.0",
    lifespan=lifespan  # lifespan 핸들러 등록
)


# 5. 루트 엔드포인트 (기존 코드)
@app.get("/")
def read_root():
    return {"Hello": "Welcome to BIMO-BE API"}


# 6. DB 연동 API 엔드포인트 (새로 추가)

@app.post("/items/", response_model=ItemRead)
async def create_item(
        *,
        session: AsyncSession = Depends(get_session),  # 의존성 주입으로 DB 세션 받기
        item_create: ItemCreate
):
    """
    새로운 아이템 생성
    """
    # 1. 입력받은 스키마(ItemCreate)로 DB 모델(Item) 객체 생성
    db_item = Item.model_validate(item_create)

    # 2. 세션에 추가하고 DB에 커밋(저장)
    session.add(db_item)
    # await session.commit() # get_session에서 자동으로 commit/rollback 처리
    await session.refresh(db_item)  # DB에서 생성된 id 등을 다시 읽어옴

    return db_item


@app.get("/items/", response_model=List[ItemRead])
async def read_items(
        session: AsyncSession = Depends(get_session)
):
    """
    모든 아이템 조회
    """
    # 1. 'Item' 테이블의 모든 데이터를 조회하는 쿼리 실행
    result = await session.execute(select(Item))
    items = result.scalars().all()

    return items