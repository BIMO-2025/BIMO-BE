from typing import Optional, List
from pydantic import BaseModel, Field

class ReviewCreate(BaseModel):
    airline_id: str
    rating: int = Field(..., ge=1, le=5)
    content: str
    images: List[str] = []

class Review(BaseModel):
    id: str
    user_id: str
    airline_id: str
    rating: int
    content: str
    images: List[str]
    created_at: str
    user_nickname: Optional[str] = None # 조회 시 join
