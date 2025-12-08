from typing import Optional, List
from pydantic import BaseModel, Field

class Airline(BaseModel):
    id: str = Field(..., description="항공사 ID (Firestore Doc ID)")
    name: str = Field(..., description="항공사 이름")
    code: str = Field(..., description="IATA 코드")
    country: str = Field(..., description="소속 국가")
    alliance: Optional[str] = Field(None, description="항공 동맹 (Star Alliance, SkyTeam, etc.)")
    type: str = Field("FSC", description="FSC 또는 LCC")
    rating: float = Field(0.0, description="평점")
    review_count: int = Field(0, description="리뷰 수")
    logo_url: Optional[str] = Field(None, description="로고 이미지 URL")
    
class AirlineDetail(Airline):
    description: Optional[str] = Field(None, description="AI 요약 설명")
    hub_airport: Optional[str] = Field(None, description="허브 공항")
    images: List[str] = Field(default_factory=list, description="항공사 관련 이미지 리스트")

class Airport(BaseModel):
    code: str = Field(..., description="공항 코드 (IATA)")
    name: str = Field(..., description="공항 이름")
    city: str = Field(..., description="도시")
    country: str = Field(..., description="국가")
