"""
항공편 검색 및 관리 서비스
"""

import random
from datetime import datetime, timedelta
from typing import List

from app.feature.flights.flights_schemas import FlightSearchResponse, FlightSearchResult

class FlightService:
    """항공편 관련 비즈니스 로직을 처리하는 서비스 클래스"""

    def search_flights(self, origin: str, destination: str, date: str) -> FlightSearchResponse:
        """
        [Mock] 항공편 검색
        실제 Amadeus API 대신 모의 데이터를 반환합니다.
        """
        # 모의 데이터 생성
        offers = self._generate_mock_offers(origin, destination, date)
        
        return FlightSearchResponse(
            origin=origin,
            destination=destination,
            date=date,
            totalResults=len(offers),
            offers=offers
        )

    def _generate_mock_offers(self, origin: str, destination: str, date_str: str) -> List[FlightSearchResult]:
        """모의 항공편 제안 목록 생성"""
        offers = []
        airlines = [
            {"code": "KE", "name": "Korean Air"},
            {"code": "OZ", "name": "Asiana Airlines"},
            {"code": "DL", "name": "Delta Air Lines"},
            {"code": "JL", "name": "Japan Airlines"},
        ]
        
        base_date = datetime.strptime(date_str, "%Y-%m-%d")
        
        # 5~10개의 랜덤 항공편 생성
        for i in range(random.randint(5, 10)):
            airline = random.choice(airlines)
            
            # 출발 시간: 검색 날짜의 06:00 ~ 22:00 사이 랜덤
            hour = random.randint(6, 22)
            minute = random.choice([0, 15, 30, 45])
            departure_time = base_date.replace(hour=hour, minute=minute)
            
            # 비행 시간: 2시간 ~ 14시간 랜덤
            duration_hours = random.randint(2, 14)
            duration_minutes = random.choice([0, 30])
            arrival_time = departure_time + timedelta(hours=duration_hours, minutes=duration_minutes)
            
            # 가격: 200,000 ~ 2,000,000원
            price = random.randint(20, 200) * 10000
            
            offer = FlightSearchResult(
                flightNumber=f"{airline['code']}{random.randint(100, 999)}",
                airlineCode=airline["code"],
                airlineName=airline["name"],
                departureAirport=origin,
                arrivalAirport=destination,
                departureTime=departure_time,
                arrivalTime=arrival_time,
                layovers=[],  # 직항으로 가정
                price=float(price),
                currency="KRW",
                duration=f"{duration_hours}h {duration_minutes}m",
                seatsAvailable=random.randint(1, 9)
            )
            offers.append(offer)
            
        # 가격순 정렬
        offers.sort(key=lambda x: x.price)
        
        return offers

# 싱글톤 인스턴스
flight_service = FlightService()

def get_flight_service() -> FlightService:
    return flight_service
