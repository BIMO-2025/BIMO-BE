# app/core/database.py (수정됨)

from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession  # 1. sqlmodel에서는 AsyncSession만 가져옵니다.
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine  # 2. sqlalchemy에서 AsyncEngine을 가져옵니다.
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator

from app.core.config import DATABASE_URL  # core 내부이므로 경로 수정 (app.core.config)

# 비동기 엔진 생성
# echo=True는 개발 중 SQL 쿼리를 터미널에 로깅해줍니다.
async_engine: AsyncEngine = create_async_engine(DATABASE_URL, echo=True, future=True)


async def create_db_and_tables():
    """
    (개발용) 서버 시작 시 모든 테이블을 생성합니다.
    """
    async with async_engine.begin() as conn:
        # await conn.run_sync(SQLModel.metadata.drop_all) # 필요시 기존 테이블 삭제
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI 의존성 주입(Dependency)을 위한 비동기 세션 생성기
    """
    session_maker = sessionmaker(
        bind=async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()