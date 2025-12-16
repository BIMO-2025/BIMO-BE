"""
리뷰 인증 관련 유틸리티
탑승권 이미지 OCR을 통해 항공편 정보를 추출하고, 사용자의 myFlights와 비교하여 인증합니다.
"""

import re
from typing import Optional, Dict, Any, List
from datetime import datetime
from fastapi import HTTPException

from app.feature.llm.gemini_client import get_gemini_client
from app.feature.llm.llm_schemas import ImageAttachment
from app.feature.flights.my_flights_service import MyFlightsService
from app.feature.flights.flights_schemas import MyFlightSchema


class FlightInfoExtractor:
    """OCR을 통해 탑승권 이미지에서 항공편 정보를 추출하는 클래스"""
    
    def __init__(self):
        self.gemini_client = get_gemini_client()
    
    async def extract_flight_info_from_image(self, base64_image: str) -> Optional[Dict[str, Any]]:
        """
        탑승권 이미지에서 항공편 정보를 추출합니다.
        
        Args:
            base64_image: Base64로 인코딩된 이미지 데이터 URL (data:image/... 형식)
            
        Returns:
            추출된 항공편 정보 딕셔너리 또는 None (추출 실패 시)
            {
                "airline_code": "KE",
                "flight_number": "KE901",
                "departure_airport": "ICN",
                "arrival_airport": "JFK",
                "departure_date": "2025-12-20",
                "seat_class": "Economy",
                "passenger_name": "KIM MINSU"
            }
        """
        try:
            # Base64 데이터 URL에서 실제 base64 데이터만 추출
            if base64_image.startswith("data:image"):
                base64_data = base64_image.split(",")[1] if "," in base64_image else base64_image
            else:
                base64_data = base64_image
            
            # Gemini API에 OCR 요청
            prompt = """이 탑승권 이미지를 분석해서 다음 정보를 JSON 형식으로 추출해주세요:
- airline_code: 항공사 코드 (예: KE, OZ, DL)
- flight_number: 항공편 번호 (예: KE901, OZ101)
- departure_airport: 출발 공항 코드 (예: ICN, JFK)
- arrival_airport: 도착 공항 코드 (예: JFK, ICN)
- departure_date: 출발 날짜 (YYYY-MM-DD 형식)
- seat_class: 좌석 등급 (Economy, Business, First 등, 없으면 null)
- passenger_name: 탑승객 이름 (없으면 null)

JSON 형식으로만 응답해주세요. 다른 설명은 필요 없습니다.
예시:
{
  "airline_code": "KE",
  "flight_number": "KE901",
  "departure_airport": "ICN",
  "arrival_airport": "JFK",
  "departure_date": "2025-12-20",
  "seat_class": "Economy",
  "passenger_name": "KIM MINSU"
}"""
            
            image_attachment = ImageAttachment(
                mime_type="image/jpeg",
                base64_data=base64_data
            )
            
            # Gemini API 호출
            response_text = await self.gemini_client.generate(
                prompt_segments=[image_attachment, prompt],
                system_instruction="You are an expert at extracting flight information from boarding pass images. Return only valid JSON."
            )
            
            # JSON 파싱 시도
            extracted_info = self._parse_extracted_info(response_text)
            
            return extracted_info
            
        except Exception as e:
            print(f"[Review Verification] OCR 추출 실패: {e}")
            return None
    
    def _parse_extracted_info(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Gemini 응답 텍스트에서 JSON을 파싱합니다.
        """
        try:
            # JSON 블록 찾기 (```json ... ``` 또는 {...})
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
            if json_match:
                import json
                json_str = json_match.group(0)
                data = json.loads(json_str)
                
                # 필수 필드 검증
                required_fields = ["airline_code", "flight_number", "departure_airport", "arrival_airport"]
                if all(field in data and data[field] for field in required_fields):
                    return data
        except Exception as e:
            print(f"[Review Verification] JSON 파싱 실패: {e}")
        
        return None


class FlightMatcher:
    """추출된 항공편 정보와 myFlights를 비교하는 클래스"""
    
    def __init__(self, my_flights_service: MyFlightsService):
        self.my_flights_service = my_flights_service
    
    async def find_matching_flight(
        self,
        user_id: str,
        extracted_info: Dict[str, Any]
    ) -> Optional[MyFlightSchema]:
        """
        추출된 항공편 정보와 일치하는 myFlights 항공편을 찾습니다.
        
        Args:
            user_id: 사용자 ID
            extracted_info: OCR로 추출된 항공편 정보
            
        Returns:
            일치하는 MyFlightSchema 또는 None
        """
        try:
            # 사용자의 모든 myFlights 조회
            flights = await self.my_flights_service.get_flights(
                user_id=user_id,
                status="completed",  # 완료된 항공편만 확인
                limit=50  # 최근 50개만 확인
            )
            
            # 각 항공편과 비교
            for flight in flights:
                if self._matches_flight(flight, extracted_info):
                    return flight
            
            return None
            
        except Exception as e:
            print(f"[Review Verification] 항공편 매칭 실패: {e}")
            return None
    
    def _matches_flight(self, flight: MyFlightSchema, extracted_info: Dict[str, Any]) -> bool:
        """
        항공편이 추출된 정보와 일치하는지 확인합니다.
        
        매칭 조건:
        1. 항공사 코드 일치 (대소문자 무시)
        2. 항공편 번호 일치 (대소문자 무시)
        3. 출발 공항 코드 일치 (대소문자 무시)
        4. 도착 공항 코드 일치 (대소문자 무시)
        5. 출발 날짜가 ±3일 이내 (탑승권 날짜와 실제 출발 날짜 차이 허용)
        """
        if not flight.segments or len(flight.segments) == 0:
            return False
        
        # 첫 번째 segment 정보 (직항의 경우 유일한 segment)
        first_segment = flight.segments[0]
        
        # 1. 항공사 코드 비교
        extracted_airline = extracted_info.get("airline_code", "").upper().strip()
        flight_airline = first_segment.operating_carrier.upper().strip() if first_segment.operating_carrier else ""
        if extracted_airline != flight_airline:
            return False
        
        # 2. 항공편 번호 비교
        extracted_flight_num = extracted_info.get("flight_number", "").upper().strip()
        # flight_number에서 항공사 코드 제거 (예: "KE901" -> "901")
        flight_num_only = first_segment.flight_number.upper().strip() if first_segment.flight_number else ""
        # extracted_flight_num도 동일하게 처리
        if extracted_flight_num.startswith(extracted_airline):
            extracted_flight_num = extracted_flight_num[len(extracted_airline):]
        if flight_num_only.startswith(flight_airline):
            flight_num_only = flight_num_only[len(flight_airline):]
        
        if extracted_flight_num != flight_num_only:
            return False
        
        # 3. 출발 공항 비교
        extracted_dep = extracted_info.get("departure_airport", "").upper().strip()
        flight_dep = ""
        if isinstance(first_segment.departure, dict):
            flight_dep = (first_segment.departure.get("iata_code") or first_segment.departure.get("iataCode") or "").upper().strip()
        elif hasattr(first_segment.departure, "iata_code"):
            flight_dep = (first_segment.departure.iata_code or "").upper().strip()
        
        if extracted_dep and flight_dep and extracted_dep != flight_dep:
            return False
        
        # 4. 도착 공항 비교 (마지막 segment의 도착 공항)
        last_segment = flight.segments[-1]
        extracted_arr = extracted_info.get("arrival_airport", "").upper().strip()
        flight_arr = ""
        if isinstance(last_segment.arrival, dict):
            flight_arr = (last_segment.arrival.get("iata_code") or last_segment.arrival.get("iataCode") or "").upper().strip()
        elif hasattr(last_segment.arrival, "iata_code"):
            flight_arr = (last_segment.arrival.iata_code or "").upper().strip()
        
        if extracted_arr and flight_arr and extracted_arr != flight_arr:
            return False
        
        # 5. 출발 날짜 비교 (±3일 허용)
        extracted_date_str = extracted_info.get("departure_date", "")
        if extracted_date_str:
            try:
                extracted_date = datetime.strptime(extracted_date_str, "%Y-%m-%d").date()
                flight_departure_time = flight.departureTime
                if isinstance(flight_departure_time, str):
                    flight_departure_time = datetime.fromisoformat(flight_departure_time.replace("Z", "+00:00"))
                flight_date = flight_departure_time.date()
                
                date_diff = abs((extracted_date - flight_date).days)
                if date_diff > 3:  # 3일 이상 차이나면 불일치
                    return False
            except Exception:
                pass  # 날짜 파싱 실패 시 날짜 비교 건너뛰기
        
        return True


async def verify_review_with_boarding_pass(
    user_id: str,
    image_urls: List[str],
    my_flights_service: MyFlightsService
) -> bool:
    """
    리뷰에 첨부된 탑승권 이미지를 분석하여 myFlights와 일치하는지 확인합니다.
    
    Args:
        user_id: 사용자 ID
        image_urls: 리뷰에 첨부된 이미지 URL 리스트 (Base64 Data URL)
        my_flights_service: MyFlightsService 인스턴스
        
    Returns:
        인증 성공 여부 (True: 인증됨, False: 인증 실패)
    """
    if not image_urls:
        return False
    
    extractor = FlightInfoExtractor()
    matcher = FlightMatcher(my_flights_service)
    
    # 모든 이미지에서 항공편 정보 추출 시도
    for image_url in image_urls:
        # Base64 Data URL인지 확인
        if not image_url.startswith("data:image"):
            continue  # Base64 이미지가 아니면 건너뛰기
        
        # OCR로 항공편 정보 추출
        extracted_info = await extractor.extract_flight_info_from_image(image_url)
        
        if not extracted_info:
            continue  # 추출 실패 시 다음 이미지 시도
        
        # myFlights에서 일치하는 항공편 찾기
        matching_flight = await matcher.find_matching_flight(user_id, extracted_info)
        
        if matching_flight:
            print(f"[Review Verification] 인증 성공: 항공편 {extracted_info.get('flight_number')} 매칭됨")
            return True
    
    print(f"[Review Verification] 인증 실패: 일치하는 항공편을 찾을 수 없음")
    return False

