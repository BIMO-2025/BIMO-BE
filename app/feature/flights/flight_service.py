import uuid
from datetime import datetime
from typing import List, Optional
from app.core.firebase import db
from app.feature.flights.models import MyFlight, MyFlightCreate, FlightStats, FlightStatus, AirportInfo, FlightAirlineInfo

class FlightService:
    def __init__(self):
        self.collection = db.collection("flights")
        self.users_collection = db.collection("users")

    async def add_flight(self, user_id: str, flight_data: MyFlightCreate) -> MyFlight:
        # 실제로는 airline_id로 항공사 정보를, code로 공항 정보를 조회해야 함.
        # 여기서는 Mock 데이터를 채워서 리턴합니다.
        
        flight_id = str(uuid.uuid4())
        
        # Mock Airline Info (실제론 DB 조회 필요)
        airline_info = FlightAirlineInfo(
            name="Korean Air",
            code="KE",
            logo_url="https://example.com/ke.png"
        )
        
        # Mock Airport Info
        dep_info = AirportInfo(
            code=flight_data.departure_code,
            name="Departure Airport",
            city="Departure City",
            time=flight_data.departure_time
        )
        
        # 도착 시간은 출발 + 10시간으로 가정
        arrival_info = AirportInfo(
            code=flight_data.arrival_code,
            name="Arrival Airport",
            city="Arrival City",
            time=flight_data.departure_time # 실제론 계산 필요
        )

        new_flight = MyFlight(
            id=flight_id,
            user_id=user_id,
            flight_number=flight_data.flight_number,
            airline=airline_info,
            departure=dep_info,
            arrival=arrival_info,
            seat_class=flight_data.seat_class,
            status=FlightStatus.SCHEDULED,
            created_at=datetime.utcnow().isoformat()
        )
        
        # Firestore 저장
        self.collection.document(flight_id).set(new_flight.dict())
        return new_flight

    async def get_upcoming_flights(self, user_id: str) -> List[MyFlight]:
        """예정된 비행 (완료되지 않은 것들)"""
        # Firestore 복합 인덱스 필요 가능성 있음 (user_id + status)
        # 지금은 단순 로직
        docs = self.collection.where("user_id", "==", user_id).stream()
        results = []
        for doc in docs:
            data = doc.to_dict()
            if data.get("status") != FlightStatus.COMPLETED:
                results.append(MyFlight(**data))
        return results

    async def get_past_flights(self, user_id: str) -> List[MyFlight]:
        """지난 비행"""
        docs = self.collection.where("user_id", "==", user_id).stream()
        results = []
        for doc in docs:
            data = doc.to_dict()
            if data.get("status") == FlightStatus.COMPLETED:
                results.append(MyFlight(**data))
        return results

    async def get_stats(self, user_id: str) -> FlightStats:
        """비행 통계"""
        # 지난 비행들을 가져와서 계산
        past_flights = await self.get_past_flights(user_id)
        
        total_time = len(past_flights) * 600 # 데모: 건당 10시간
        total_dist = len(past_flights) * 5000 # 데모: 건당 5000km
        countries = set()
        
        return FlightStats(
            total_flight_time_minutes=total_time,
            total_distance_km=total_dist,
            visited_countries_count=len(countries)
        )
