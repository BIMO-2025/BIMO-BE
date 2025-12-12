"""
항공편 검색 관련 비즈니스 로직
"""

from typing import List, Dict
from fastapi.concurrency import run_in_threadpool

from app.core.firebase import FirebaseService
from app.core.exceptions.exceptions import ExternalApiError
from app.feature.flights.flights_schemas import (
    FlightOfferSchema,
    FlightSearchRequest,
    FlightSearchResponse,
    LocationSchema,
    LocationSearchResponse,
)


class FlightsService:
    """항공편 검색 관련 비즈니스 로직을 처리하는 서비스 클래스"""
    
    def __init__(self, amadeus_client, firebase_service: FirebaseService):
        """
        FlightsService 초기화
        
        Args:
            amadeus_client: Amadeus API 클라이언트 인스턴스
            firebase_service: Firebase 서비스 인스턴스
        """
        self.amadeus_client = amadeus_client
        self.firebase_service = firebase_service
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

    async def search_flights(self, request: FlightSearchRequest) -> FlightSearchResponse:
        """
        Amadeus API를 사용하여 항공편을 검색하고 항공사 정보를 포함하여 반환합니다.
        """
        try:
            # 1. Amadeus API 호출
            flight_data = await self.amadeus_client.search_flights(
                origin=request.origin,
                destination=request.destination,
                departure_date=request.departure_date,
                adults=request.adults,
            )


            if not isinstance(flight_data, list):
                flight_data = flight_data if isinstance(flight_data, list) else []

            # 2. 결과 파싱 및 기본 데이터 구성
            flight_offers = []
            parsing_failed_count = 0
            
            # 필요한 항공사 코드 수집 (중복 제거)
            airline_codes = set()

            for offer in flight_data:
                try:
                    flight_offer = FlightOfferSchema(**offer)
                    
                    # 유효한 항공사 코드 수집
                    # 1. validating_airline_codes에서 추출
                    if flight_offer.validating_airline_codes:
                        airline_codes.add(flight_offer.validating_airline_codes[0])
                    
                    # 2. segments의 carrierCode에서도 추출 (validating_airline_codes가 없는 경우 대비)
                    for itinerary in flight_offer.itineraries:
                        for segment in itinerary.segments:
                            if segment.carrier_code:
                                airline_codes.add(segment.carrier_code)
                    
                    # 직항/경유 정보 계산
                    total_segments = 0
                    for itinerary in flight_offer.itineraries:
                        total_segments += len(itinerary.segments)
                    
                    # 편도 기준: 세그먼트가 1개면 직항
                    # 왕복의 경우 로직이 복잡해질 수 있으나, 현재는 편도 검색만 지원한다고 가정
                    is_direct = False
                    stopover_text = ""
                    
                    # 첫 번째 여정 기준 (편도)
                    if flight_offer.itineraries:
                        segments_count = len(flight_offer.itineraries[0].segments)
                        if segments_count == 1:
                            is_direct = True
                            stopover_text = "직항"
                        else:
                            is_direct = False
                            stopover_text = f"{segments_count - 1}회 경유"
                    
                    flight_offer.is_direct = is_direct
                    flight_offer.stopover_info = stopover_text
                    
                    flight_offers.append(flight_offer)
                except Exception as e:
                    parsing_failed_count += 1
                    continue

            # 3. 항공사 추가 정보(평점, 리뷰 등) 조회 및 매핑
            # 지연 임포트로 순환 참조 방지
            from app.feature.airlines.airline_service import AirlineService
            
            airline_service = AirlineService(firebase_service=self.firebase_service)
            airline_stats_map = {}
            for code in airline_codes:
                # 병렬 처리하면 좋겠지만, 일단 순차 처리 (캐싱 고려 가능)
                try:
                    stats = await airline_service.get_airline_statistics(code)
                    if stats:
                        airline_stats_map[code] = stats
                except Exception:
                    # 개별 항공사 조회 실패해도 전체 로직은 진행
                    continue
            
            # 4. 결과에 항공사 정보 주입
            for offer in flight_offers:
                # 1. validating_airline_codes에서 항공사 코드 추출 시도
                airline_code = None
                if offer.validating_airline_codes:
                    airline_code = offer.validating_airline_codes[0]
                
                # 2. validating_airline_codes가 없으면 segments의 carrierCode 사용
                if not airline_code and offer.itineraries:
                    for itinerary in offer.itineraries:
                        for segment in itinerary.segments:
                            if segment.carrier_code:
                                airline_code = segment.carrier_code
                                break
                        if airline_code:
                            break
                
                # 3. 항공사 정보 주입
                if airline_code and airline_code in airline_stats_map:
                    offer.airline_info = airline_stats_map[airline_code]
            
            # 4-1. 검색 결과에 포함된 항공사 목록 생성 (중복 제거, overallRating 내림차순 정렬)
            unique_airlines = list(airline_stats_map.values())
            sorted_airlines = sorted(
                unique_airlines,
                key=lambda x: x.overallRating if x else 0.0,
                reverse=True
            )
            
            # 5. 정렬 (기본값: overallRating 내림차순, 요청된 경우 해당 정렬 적용)
            if request.sort_by:
                if request.sort_by == "rating_desc":
                    flight_offers.sort(
                        key=lambda x: x.airline_info.overallRating if x.airline_info else 0.0, 
                        reverse=True
                    )
                elif request.sort_by == "review_count_desc":
                    flight_offers.sort(
                        key=lambda x: x.airline_info.totalReviews if x.airline_info else 0, 
                        reverse=True
                    )
                elif request.sort_by == "price_asc":
                    # 가격 정렬 (문자열이므로 float 변환 필요)
                    flight_offers.sort(
                        key=lambda x: float(x.price.total) if x.price.total else float('inf')
                    )
            else:
                # 기본 정렬: overallRating 내림차순
                flight_offers.sort(
                    key=lambda x: x.airline_info.overallRating if x.airline_info else 0.0, 
                    reverse=True
                )

            # 클라이언트에게 반환할 때 불필요한 필드 제외
            excluded_fields = {
                "id",
                "source",
                "instant_ticketing_required",
                "non_homogeneous",
                "last_ticketing_date",
                "validating_airline_codes",
                "traveler_pricings",
                "airline_info"  # airline_info는 내부적으로만 사용하고, overallRating만 노출
            }
            
            # 각 flight_offer를 dict로 변환하면서 제외할 필드 제거 및 duration 포맷팅
            filtered_offers = []
            for offer in flight_offers:
                offer_dict = offer.model_dump(exclude=excluded_fields, exclude_none=True, by_alias=True)
                
                # overallRating을 항공편 결과에 직접 추가
                if offer.airline_info and offer.airline_info.overallRating is not None:
                    offer_dict["overallRating"] = offer.airline_info.overallRating
                else:
                    offer_dict["overallRating"] = 0.0
                
                # 각 itinerary의 duration 포맷팅
                if "itineraries" in offer_dict:
                    for itinerary in offer_dict["itineraries"]:
                        # itinerary의 duration 포맷팅
                        if "duration" in itinerary:
                            itinerary["duration"] = self._format_duration(itinerary["duration"])
                        
                        # segments의 duration 포맷팅
                        if "segments" in itinerary:
                            for segment in itinerary["segments"]:
                                if "duration" in segment and segment["duration"]:
                                    segment["duration"] = self._format_duration(segment["duration"])
                
                filtered_offers.append(offer_dict)

            return FlightSearchResponse(
                flight_offers=filtered_offers,  # dict 리스트로 반환
                count=len(filtered_offers),
                airlines=sorted_airlines,  # 항공사 목록 추가 (overallRating 내림차순)
            )

        except ExternalApiError:
            raise
        except Exception as e:
            raise ExternalApiError(
                provider="Amadeus",
                detail=f"항공편 검색 중 오류가 발생했습니다: {str(e)}",
            ) from e

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
        키워드를 기반으로 공항 및 도시를 검색합니다.
        1) 로컬 Firestore 'airports' 컬렉션 우선 검색 (오프라인/캐시된 추천)
        2) Amadeus API 검색 결과를 병합 (중복 IATA 제거)
        """
        try:
            combined: List[LocationSchema] = []
            seen_codes = set()

            # 1) 로컬 검색
            local_locations = await self._search_local_airports(keyword)
            for loc in local_locations:
                if loc.iata_code not in seen_codes:
                    seen_codes.add(loc.iata_code)
                    combined.append(loc)

            # 2) Amadeus API 호출 (보조)
            locations_data = await self.amadeus_client.search_locations(
                keyword=keyword,
                sub_type=["AIRPORT", "CITY"],
            )

            for loc in locations_data:
                try:
                    subtype = loc.get("subType", "").upper()
                    iata = loc.get("iataCode", "")
                    if iata in seen_codes:
                        continue
                    location_schema = LocationSchema(
                        id=loc.get("id"),
                        name=loc.get("name", ""),
                        detailed_name=loc.get("detailedName"),
                        iata_code=iata,
                        geo_code=loc.get("geoCode"),
                        address=loc.get("address"),
                        sub_type=subtype,
                    )
                    combined.append(location_schema)
                    seen_codes.add(iata)
                except Exception as e:
                    print(f"위치 데이터 파싱 실패: {e}")
                    continue

            return LocationSearchResponse(
                locations=combined,
                count=len(combined),
            )

        except ExternalApiError:
            raise
        except Exception as e:
            raise ExternalApiError(
                provider="Amadeus",
                detail=f"위치 검색 중 오류가 발생했습니다: {str(e)}",
            ) from e

