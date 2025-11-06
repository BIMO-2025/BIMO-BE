from pydantic import BaseModel, ConfigDict


# --- 기본 스키마 ---
# API의 Request/Response에서 공통적으로 사용할 필드를 정의
class TestBase(BaseModel):
    name: str
    age: int


# --- Request 스키마 ---
# POST (생성) 요청 시 Request Body로 받을 데이터의 형태
# TestBase를 상속받으므로 name과 age 필드를 가집니다.
class TestCreate(TestBase):
    pass  # 생성 시에는 id가 필요 없으므로 TestBase와 동일


# --- Response 스키마 ---
# GET (조회) 요청 시 Response Body로 보낼 데이터의 형태
# id는 데이터베이스에서 자동 생성되므로, 응답 시에는 포함되어야 함
class TestSchema(TestBase):
    id: int

    # SQLAlchemy 모델 객체(models.Test)를 Pydantic 스키마로
    # 자동으로 변환(매핑)할 수 있도록 허용하는 설정
    # Pydantic V2 (최신) 기준입니다.
    model_config = ConfigDict(from_attributes=True)