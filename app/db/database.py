from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import DATABASE_URL

# 1. 데이터베이스 URL 정의
# "어떤 DB(postgresql)에, 어떤 계정(admin:1234)으로함
# 어디(localhost:5432)에 있는, 무슨 DB(BIMO_DB)에 접속할지"를 명시
# DATABASE_URL = "postgresql://admin:1234@localhost:5432/BIMO_DB"

# 2. Engine 생성
# create_engine() 함수는 DATABASE_URL 정보를 바탕으로
# Engine 객체를 생성하여 반환
# 이 'engine' 객체가 커넥션 풀을 관리
engine = create_engine(DATABASE_URL)

# 3. Session 팩토리(Factory) 생성
# sessionmaker는 'Session 클래스'를 만들어내는 클래스(팩토리)
# 'SessionLocal'은 아직 세션 객체 '자체'가 아니라,세션을 만들어내는 class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# - autocommit=False: 자동으로 commit하지 않도록 설정 (우리가 직접 db.commit() 호출)
# - autoflush=False: 자동으로 flush(변경사항을 DB에 임시 반영)하지 않도록 설정
# - bind=engine: 이 세션 팩토리가 'engine'을 사용하여
#               DB 연결(커넥션 풀)을 가져오도록 바인딩(연결)

# 4. ORM 모델용 Base 클래스 생성
# declarative_base()는 'Base'라는 기본 클래스를 반환
Base = declarative_base()