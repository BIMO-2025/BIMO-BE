# app/models/item_model.py (새 파일)

from sqlmodel import SQLModel, Field

# 1. API 입출력용 기본 스키마 (Pydantic 모델 역할)
class ItemBase(SQLModel):
    name: str = Field(index=True) # index=True는 이 컬럼을 검색 가능하게 함
    description: str | None = None

# 2. DB 테이블 정의 (SQLAlchemy 모델 역할)
# 'table=True'가 이 클래스를 DB 테이블과 매핑시킵니다.
class Item(ItemBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

# 3. 데이터 생성(Create) 시 사용할 스키마
# (id는 DB가 자동 생성하므로 입력받지 않음)
class ItemCreate(ItemBase):
    pass

# 4. 데이터 조회(Read) 시 사용할 스키마
# (id를 포함하여 반환)
class ItemRead(ItemBase):
    id: int