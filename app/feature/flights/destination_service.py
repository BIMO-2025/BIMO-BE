from typing import List
from app.core.firebase import db
from app.feature.airlines.models import Airport

class DestinationService:
    def __init__(self):
        self.collection = db.collection("airports")

    async def search_destinations(self, query: str) -> List[Airport]:
        """
        목적지(국가, 도시, 공항명, 공항코드) 검색
        """
        if not query:
            return []

        # 데모: 전체 조회 후 필터링
        docs = self.collection.stream()
        results = []
        q = query.lower()
        
        for doc in docs:
            data = doc.to_dict()
            # 검색 조건: 이름, 도시, 국가, 코드 중 하나라도 포함되면
            if (q in data.get("name", "").lower() or
                q in data.get("city", "").lower() or
                q in data.get("country", "").lower() or
                q in data.get("code", "").lower()):
                results.append(Airport(**data))
        return results
