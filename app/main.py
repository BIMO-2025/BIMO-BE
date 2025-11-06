from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

# 준비한 파일들에서 필요한 것들을 임포트합니다.
# (파일 경로가 app/ 디렉토리 기준이라고 가정합니다.)
from app.db import models, database
from app.db.schemas import TestSchema, TestCreate

# --- DB 테이블 생성 ---
# FastAPI 애플리케이션이 시작될 때, models.Base를 상속받은
# 모든 클래스(지금은 Test)를 찾아 데이터베이스에 테이블을 생성합니다.
# (이미 테이블이 존재하면 아무 동작도 하지 않습니다.)
models.Base.metadata.create_all(bind=database.engine)

# FastAPI 앱 인스턴스 생성
app = FastAPI()


# --- 의존성 주입 함수 (Dependency) ---
# database.py의 SessionLocal을 사용하여 DB 세션을 생성하고
# API 처리가 끝나면 항상 세션을 닫아(close) 자원을 반환합니다.
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- API 엔드포인트 구현 ---

@app.post("/test/", response_model=TestSchema)
def create_test_data(test: TestCreate, db: Session = Depends(get_db)):
    """
    새로운 test 데이터를 생성합니다. (Create)
    - Request Body로 TestCreate 스키마 형태의 JSON을 받습니다.
    - Response Body로 TestSchema 형태의 JSON을 반환합니다.
    """
    # 1. Pydantic 스키마(test)를 dict로 변환하고,
    #    SQLAlchemy 모델(models.Test)의 인스턴스를 생성합니다.
    db_test = models.Test(**test.model_dump())

    # 2. 세션(작업 공간)에 모델 인스턴스를 추가합니다.
    db.add(db_test)

    # 3. 변경 사항을 DB에 커밋(반영)합니다.
    db.commit()

    # 4. DB에서 방금 생성된 데이터(e.g., 자동 생성된 id)를 
    #    포함하여 객체를 새로고침합니다.
    db.refresh(db_test)

    # 5. 생성된 SQLAlchemy 모델 객체를 반환합니다.
    #    (FastAPI가 response_model(TestSchema)을 보고
    #     자동으로 JSON으로 변환해줍니다.)
    return db_test


@app.get("/test/", response_model=List[TestSchema])
def read_all_test_data(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """
    모든 test 데이터를 조회합니다. (Read - List)
    - skip, limit 쿼리 파라미터로 페이징
    - Response Body로 TestSchema의 리스트(List)를 반환합니다.
    """
    # db.query(models.Test): 'test' 테이블을 대상으로 쿼리
    # .offset(skip).limit(limit): 페이징
    # .all(): 모든 결과를 리스트로 가져옵니다.
    tests = db.query(models.Test).offset(skip).limit(limit).all()
    return tests


@app.get("/test/{test_id}", response_model=TestSchema)
def read_one_test_data(test_id: int, db: Session = Depends(get_db)):
    """
    특정 ID의 test 데이터를 조회합니다. (Read - One)
    - test_id를 URL 경로(Path) 파라미터로 받습니다.
    """
    # 'test' 테이블에서 id가 'test_id'와 일치하는 첫 번째 데이터를 찾습니다.
    db_test = db.query(models.Test).filter(models.Test.id == test_id).first()

    # 데이터가 없으면 404 Not Found 오류를 발생시킵니다.
    if db_test is None:
        raise HTTPException(status_code=404, detail="Test data not found")

    return db_test