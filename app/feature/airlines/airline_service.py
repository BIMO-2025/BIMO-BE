from typing import List, Optional
from app.core.firebase import db
from app.feature.airlines.models import Airline, AirlineDetail

class AirlineService:
    def __init__(self):
        self.collection = db.collection("airlines")

    async def search_airlines(self, query: str) -> List[Airline]:
        """
        항공사 이름으로 검색 (Firestore는 full-text search가 약하므로
        실제론 Algolia 등을 쓰거나, 여기선 단순 startswith/equality 데모)
        """
        # 실제 구현: 부분 일치 검색을 위해선 별도 인덱싱 필요.
        # 여기서는 단순 쿼리 예시
        if not query:
            return []
            
        # 데모 로직: 전체 다 가져와서 필터링 (데이터가 적다는 가정)
        # 프로덕션에서는 절대 이렇게 하면 안됨.
        docs = self.collection.stream()
        results = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            if query.lower() in data.get("name", "").lower():
                results.append(Airline(**data))
        return results

    async def get_popular_airlines(self, limit: int = 5) -> List[Airline]:
        """인기 항공사 조회 (평점 높은 순)"""
        docs = self.collection.order_by(
            "rating", direction="DESCENDING"
        ).limit(limit).stream()
        
        return [Airline(**doc.to_dict(), id=doc.id) for doc in docs]

    async def get_airline_detail(self, airline_id: str) -> Optional[AirlineDetail]:
        """항공사 상세 정보 조회"""
        doc = self.collection.document(airline_id).get()
        if not doc.exists:
            return None
        return AirlineDetail(**doc.to_dict(), id=doc.id)
