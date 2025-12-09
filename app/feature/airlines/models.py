from typing import Optional, List
from pydantic import BaseModel, Field


class Airline(BaseModel):
    """항공사 기본 정보"""
    id: str = Field(..., description="항공사 ID (Firestore Doc ID = airlineCode)")
    name: str = Field(..., description="항공사 이름")
    code: str = Field(..., description="IATA 코드")
    country: str = Field(..., description="소속 국가")
    alliance: Optional[str] = Field(None, description="항공 동맹 (Star Alliance, SkyTeam, etc.)")
    type: str = Field("FSC", description="FSC 또는 LCC")
    rating: float = Field(0.0, description="평점")
    review_count: int = Field(0, description="리뷰 수")
    logo_url: Optional[str] = Field(None, description="로고 이미지 URL")


class AirlineDetail(Airline):
    """항공사 상세 정보 (화면 표시용)"""
    # 기본 정보
    name_en: Optional[str] = Field(None, description="항공사 영어 이름")
    hub_airport: Optional[str] = Field(None, description="허브 공항 코드")
    hub_airport_name: Optional[str] = Field(None, description="허브 공항 이름")
    operating_classes: List[str] = Field(default_factory=list, description="운항 클래스 리스트")
    images: List[str] = Field(default_factory=list, description="항공사 관련 이미지 리스트")
    
    # 집계 통계
    total_reviews: int = Field(0, description="총 리뷰 개수")
    average_ratings: dict = Field(default_factory=dict, description="카테고리별 평균 평점")
    rating_breakdown: dict = Field(default_factory=dict, description="카테고리별 점수 분포")
    overall_rating: float = Field(0.0, description="전체 평균 평점")
    
    # 추가 정보
    description: Optional[str] = Field(None, description="항공사 설명")


class Airport(BaseModel):
    """공항 정보"""
    code: str = Field(..., description="공항 코드 (IATA)")
    name: str = Field(..., description="공항 이름")
    city: str = Field(..., description="도시")
    country: str = Field(..., description="국가")

