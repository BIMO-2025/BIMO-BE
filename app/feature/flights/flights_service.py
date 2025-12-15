"""
항공편 검색 관련 비즈니스 로직
"""

import logging
from typing import List, Dict
from fastapi.concurrency import run_in_threadpool

from app.core.firebase import FirebaseService
from app.core.exceptions.exceptions import ExternalApiError

# 로거 설정
logger = logging.getLogger(__name__)
from app.feature.flights.flights_schemas import (
    FlightOfferSchema,
    FlightSearchRequest,
    FlightSearchResponse,
    LocationSchema,
    LocationSearchResponse,
    AirlineSearchRequest,
    AirlineSearchResponse,
    AirlineSearchResponseItem,
    SegmentDetailSchema,
    AirportIATASearchRequest,
    AirportIATASearchResponse,
    AirportIATAResult,
)


class FlightsService:
    """항공편 검색 관련 비즈니스 로직을 처리하는 서비스 클래스"""
    
    def __init__(self, duffel_client=None, firebase_service: FirebaseService = None):
        """
        FlightsService 초기화
        
        Args:
            duffel_client: Duffel API 클라이언트 인스턴스
            firebase_service: Firebase 서비스 인스턴스
        """
        self.duffel_client = duffel_client
        self.firebase_service = firebase_service
        if firebase_service:
            self.db = firebase_service.db
            self.airports_collection = self.db.collection("airports")
    
    @staticmethod
    def _format_duration(duration: str) -> str:
        """
        ISO 8601 duration 형식(PT35H14M)을 간단한 형식(35H14M)으로 변환
        
        Args:
            duration: ISO 8601 duration 문자열 (예: "PT35H14M")
            
        Returns:
            변환된 duration 문자열 (예: "35H14M")
        """
        if not duration:
            return duration
        
        # "PT" prefix 제거
        if duration.startswith("PT"):
            return duration[2:]
        return duration


    async def _search_local_airports(self, keyword: str) -> List[LocationSchema]:
        """
        Firestore 'airports' 컬렉션에서 한글/영어/코드 기반 부분 검색.
        """
        keyword_lower = keyword.lower()

        def _fetch():
            return list(self.airports_collection.stream())

        docs = await run_in_threadpool(_fetch)
        results: List[LocationSchema] = []

        for doc in docs:
            data = doc.to_dict()
            # 다중 필드 부분 매칭
            candidates = [
                data.get("name", ""),
                data.get("name_en", ""),
                data.get("name_ko", ""),
                data.get("city", ""),
                data.get("city_en", ""),
                data.get("city_ko", ""),
                data.get("country", ""),
                data.get("country_en", ""),
                data.get("country_ko", ""),
                data.get("code", ""),
            ]
            if not any(keyword_lower in str(c).lower() for c in candidates):
                continue

            address = {
                "cityName": data.get("city_ko") or data.get("city_en"),
                "countryName": data.get("country_ko") or data.get("country_en"),
            }

            loc = LocationSchema(
                id=data.get("code"),
                name=data.get("name", ""),
                detailed_name=None,
                iata_code=data.get("code", ""),
                geo_code=None,
                address=address,
                sub_type="AIRPORT",
            )
            results.append(loc)

        return results

    async def search_locations(self, keyword: str) -> LocationSearchResponse:
        """
        키워드를 기반으로 공항을 검색합니다.
        로컬 Firestore 'airports' 컬렉션에서만 검색합니다.
        """
        try:
            # 로컬 검색만 수행
            local_locations = await self._search_local_airports(keyword)

            return LocationSearchResponse(
                locations=local_locations,
                count=len(local_locations),
            )

        except Exception as e:
            raise ExternalApiError(
                provider="Local",
                detail=f"위치 검색 중 오류가 발생했습니다: {str(e)}",
            ) from e

    @staticmethod
    def _extract_operating_carrier(segment: Dict) -> str | None:
        """
        segment에서 operating_carrier 추출
        
        Args:
            segment: segment 딕셔너리
            
        Returns:
            operating_carrier 코드 또는 None
        """
        # 여러 가능한 경로 시도
        if isinstance(segment.get("operating_carrier_iata"), str):
            return segment["operating_carrier_iata"]
        
        if isinstance(segment.get("operating_carrier"), str):
            return segment["operating_carrier"]
        
        # 중첩 객체인 경우
        operating_carrier_obj = segment.get("operating_carrier")
        if isinstance(operating_carrier_obj, dict):
            return operating_carrier_obj.get("iata_code") or operating_carrier_obj.get("iata")
        
        # marketing_carrier로 대체
        if isinstance(segment.get("marketing_carrier_iata"), str):
            return segment["marketing_carrier_iata"]
        
        marketing_carrier_obj = segment.get("marketing_carrier")
        if isinstance(marketing_carrier_obj, dict):
            return marketing_carrier_obj.get("iata_code") or marketing_carrier_obj.get("iata")
        
        return None

    @staticmethod
    def _extract_logo_symbol_url(segment: Dict) -> str | None:
        """
        segment에서 logo_symbol_url 추출 (Duffel API 응답에서)
        
        Args:
            segment: segment 딕셔너리
            
        Returns:
            logo_symbol_url 또는 None
        """
        # operating_carrier 객체에서 logo_symbol_url 추출
        operating_carrier_obj = segment.get("operating_carrier")
        if isinstance(operating_carrier_obj, dict):
            logo_url = operating_carrier_obj.get("logo_symbol_url")
            if logo_url:
                return logo_url
        
        # airline 객체에서 logo_symbol_url 추출
        airline_obj = segment.get("airline")
        if isinstance(airline_obj, dict):
            logo_url = airline_obj.get("logo_symbol_url")
            if logo_url:
                return logo_url
        
        return None

    @staticmethod
    def _is_same_operating_carrier(segments: List[Dict]) -> bool:
        """
        모든 segment의 operating_carrier가 동일한지 확인
        
        Args:
            segments: segment 리스트
            
        Returns:
            모든 segment의 operating_carrier가 동일하면 True
        """
        if not segments:
            return False
        
        first_carrier = None
        for segment in segments:
            operating_carrier = FlightsService._extract_operating_carrier(segment)
            if not operating_carrier:
                return False
            
            if first_carrier is None:
                first_carrier = operating_carrier
            elif operating_carrier != first_carrier:
                return False
        
        return True

    @staticmethod
    def _parse_duration_seconds(seconds: int) -> str:
        """
        초 단위 duration을 HMM 형식으로 변환
        
        Args:
            seconds: 초 단위 시간
            
        Returns:
            "14H30M" 형식의 문자열
        """
        if not seconds:
            return "0M"
        
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        
        if hours > 0 and minutes > 0:
            return f"{hours}H{minutes}M"
        elif hours > 0:
            return f"{hours}H"
        else:
            return f"{minutes}M"
    
    @staticmethod
    def _parse_iso_duration(iso_duration: str) -> str:
        """
        ISO 8601 duration 형식(PT14H30M)을 HMM 형식(14H30M)으로 변환
        
        Args:
            iso_duration: ISO 8601 duration 문자열 (예: "PT14H30M", "PT2H30M")
            
        Returns:
            "14H30M" 형식의 문자열
        """
        if not iso_duration:
            return "0M"
        
        # "PT" prefix 제거
        duration_str = iso_duration.replace("PT", "")
        
        hours = 0
        minutes = 0
        
        # 시간 추출
        if "H" in duration_str:
            hours_part = duration_str.split("H")[0]
            try:
                hours = int(hours_part)
            except ValueError:
                pass
        
        # 분 추출
        if "M" in duration_str:
            minutes_part = duration_str.split("H")[-1].split("M")[0] if "H" in duration_str else duration_str.split("M")[0]
            try:
                minutes = int(minutes_part)
            except ValueError:
                pass
        
        if hours > 0 and minutes > 0:
            return f"{hours}H{minutes}M"
        elif hours > 0:
            return f"{hours}H"
        elif minutes > 0:
            return f"{minutes}M"
        else:
            return "0M"
    
    @staticmethod
    def _extract_duration(segment_or_slice: Dict) -> str:
        """
        segment 또는 slice에서 duration 추출 (여러 형식 지원)
        
        Args:
            segment_or_slice: segment 또는 slice 딕셔너리
            
        Returns:
            "14H30M" 형식의 duration 문자열
        """
        
        duration_iso = segment_or_slice.get("duration")
        if duration_iso:
            return FlightsService._parse_iso_duration(duration_iso)
        
        # 3. 둘 다 없으면 0M 반환
        return "0M"

    async def search_airlines(self, request: AirlineSearchRequest) -> AirlineSearchResponse:
        """
        Duffel API를 사용하여 항공편을 검색하고, 동일한 operating carrier만 필터링하여 반환합니다.
        
        Args:
            request: 항공사 검색 요청 (departure, arrive, departure_date)
            
        Returns:
            동일한 operating carrier를 가진 항공편 목록
        """
        if not self.duffel_client:
            raise ExternalApiError(
                provider="Duffel",
                detail="Duffel 클라이언트가 초기화되지 않았습니다.",
            )
        
        try:
            # 1. Duffel API 호출
            response_data = await self.duffel_client.search_offers(
                origin=request.departure,
                destination=request.arrive,
                departure_date=request.departure_date,
                adults=1,
            )
            
            # 2. 응답에서 offers 추출
            offers = response_data.get("data", {}).get("offers", [])
            if not offers:
                return AirlineSearchResponse(count=0, results=[])
            
            # 3. 동일한 operating carrier만 필터링
            filtered_results = []
            
            for offer in offers:
                try:
                    # offer의 첫 번째 slice (편도 검색이므로 하나만 있음)
                    slices = offer.get("slices", [])
                    if not slices:
                        continue
                    
                    first_slice = slices[0]
                    segments = first_slice.get("segments", [])
                    
                    if not segments:
                        continue
                    
                    # 동일한 operating carrier 확인
                    if not self._is_same_operating_carrier(segments):
                        continue
                    
                    # 첫 번째 segment의 operating carrier 추출
                    first_segment = segments[0]
                    operating_carrier = self._extract_operating_carrier(first_segment)
                    
                    if not operating_carrier:
                        continue
                    
                    # 경유 여부 확인 (segment가 1개면 직항, 2개 이상이면 경유)
                    has_stopover = len(segments) > 1
                    
                    # 첫 번째 segment에서 logo_symbol_url 추출 (Duffel API 응답에서)
                    logo_symbol_url = self._extract_logo_symbol_url(first_segment)
                    
                    # 항공편명 생성 헬퍼 함수
                    def get_flight_number(segment: Dict, carrier: str) -> str:
                        """operating_carrier IATA 코드 + operating_carrier_flight_number로 항공편명 생성"""
                        flight_number = segment.get("operating_carrier_flight_number") or segment.get("flight_number")
                        if flight_number:
                            return f"{carrier}{flight_number}"
                        return f"{carrier}000"  # 기본값
                    
                    # 첫 번째 segment의 항공편명 추출
                    first_flight_number = get_flight_number(first_segment, operating_carrier)
                    
                    # 총 비행 시간 계산 (slice에서 duration 추출)
                    total_duration = self._extract_duration(first_slice)
                    
                    # 각 segment 정보 추출
                    segment_details = []
                    for segment in segments:
                        # segment에서 duration 추출 (duration_seconds 또는 duration 지원)
                        segment_duration = self._extract_duration(segment)
                        
                        segment_operating_carrier = self._extract_operating_carrier(segment) or operating_carrier
                        segment_flight_number = get_flight_number(segment, segment_operating_carrier)
                        
                        # departure와 arrival 정보 추출
                        departure_info = segment.get("departing_at")
                        arrival_info = segment.get("arriving_at")
                        
                        # 문자열인 경우 dict로 변환
                        if isinstance(departure_info, str):
                            departure_info = {"at": departure_info, "iata_code": segment.get("origin", {}).get("iata_code") or segment.get("origin_iata_code")}
                        elif not isinstance(departure_info, dict):
                            departure_info = {}
                        
                        if isinstance(arrival_info, str):
                            arrival_info = {"at": arrival_info, "iata_code": segment.get("destination", {}).get("iata_code") or segment.get("destination_iata_code")}
                        elif not isinstance(arrival_info, dict):
                            arrival_info = {}
                        
                        segment_details.append(
                            SegmentDetailSchema(
                                operating_carrier=segment_operating_carrier,
                                flight_number=segment_flight_number,
                                duration=segment_duration,
                                departure=departure_info,
                                arrival=arrival_info,
                            )
                        )
                    
                    filtered_results.append(
                        AirlineSearchResponseItem(
                            operating_carrier=operating_carrier,
                            logo_symbol_url=logo_symbol_url,
                            has_stopover=has_stopover,
                            flight_number=first_flight_number,
                            total_duration=total_duration,
                            segments=segment_details,
                        )
                    )
                    
                except Exception as e:
                    logger.warning(f"Offer 파싱 실패: {str(e)}")
                    continue
            
            return AirlineSearchResponse(
                count=len(filtered_results),
                results=filtered_results,
            )
            
        except ExternalApiError:
            raise
        except Exception as e:
            raise ExternalApiError(
                provider="Duffel",
                detail=f"항공편 검색 중 오류가 발생했습니다: {str(e)}",
            ) from e

    async def search_airport_iata_code(self, request: AirportIATASearchRequest) -> AirportIATASearchResponse:
        """
        Duffel API를 사용하여 위치 정보로 공항 IATA 코드를 검색합니다.
        
        Args:
            request: 공항 IATA 코드 검색 요청 (location)
            
        Returns:
            검색된 공항 IATA 코드 목록
        """
        if not self.duffel_client:
            raise ExternalApiError(
                provider="Duffel",
                detail="Duffel 클라이언트가 초기화되지 않았습니다.",
            )
        
        try:
            # location을 그대로 쿼리로 사용
            query = request.location.strip()
            
            if not query:
                raise ExternalApiError(
                    provider="Duffel",
                    detail="위치 정보는 필수입니다.",
                )
            
            # 1. Duffel API 호출
            places = await self.duffel_client.search_places(query=query)
            
            if not places:
                return AirportIATASearchResponse(count=0, results=[])
            
            # 2. 공항 타입만 필터링 및 IATA 코드 추출
            airport_results = []
            seen_iata_codes = set()
            
            for place in places:
                try:
                    # type이 "airport"인 것만 필터링
                    place_type = place.get("type", "").lower()
                    if place_type != "airport":
                        continue
                    
                    # IATA 코드 추출
                    iata_code = place.get("iata_code") or place.get("iata")
                    if not iata_code:
                        continue
                    
                    # 중복 제거
                    if iata_code in seen_iata_codes:
                        continue
                    seen_iata_codes.add(iata_code)
                    
                    # 추가 정보 추출
                    city = place.get("city", {}).get("name") if isinstance(place.get("city"), dict) else place.get("city")
                    country = place.get("country", {}).get("name") if isinstance(place.get("country"), dict) else place.get("country")
                    name = place.get("name")
                    
                    airport_results.append(
                        AirportIATAResult(
                            iata_code=iata_code,
                            city=city,
                            country=country,
                            name=name,
                        )
                    )
                    
                except Exception as e:
                    logger.warning(f"Place 파싱 실패: {str(e)}")
                    continue
            
            return AirportIATASearchResponse(
                count=len(airport_results),
                results=airport_results,
            )
            
        except ExternalApiError:
            raise
        except Exception as e:
            raise ExternalApiError(
                provider="Duffel",
                detail=f"공항 IATA 코드 검색 중 오류가 발생했습니다: {str(e)}",
            ) from e

