# postgresql에 있는 table을 Python Class로 mapping 해주는 코드
# Test(=Python Class) : test(=Postgresql table) mapping

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String
from app.db.database import Base

class Test(Base):
    __tablename__ = "test"

    id : Mapped[int] = mapped_column(Integer, primary_key=True)
    name : Mapped[str] = mapped_column(String(15))
    age : Mapped[int] = mapped_column(Integer)
