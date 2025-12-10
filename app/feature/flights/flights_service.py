"""
항공편 검색 관련 비즈니스 로직
"""

from typing import List
from fastapi.concurrency import run_in_threadpool

from app.core.clients.amadeus import amadeus_client
from app.core.exceptions.exceptions import ExternalApiError
from app.core.firebase import db
from app.feature.flights.flights_schemas import (
    FlightOfferSchema,
    FlightSearchRequest,
    FlightSearchResponse,
    LocationSchema,
    LocationSearchResponse,
)


airports_collection = db.collection("airports")


async def search_flights(request: FlightSearchRequest) -> FlightSearchResponse:
    """
    Amadeus API를 사용하여 항공편을 검색하고 항공사 정보를 포함하여 반환합니다.
    """
    try:
        # 1. Amadeus API 호출
        flight_data = await amadeus_client.search_flights(
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
                if flight_offer.validating_airline_codes:
                    airline_codes.add(flight_offer.validating_airline_codes[0])
                
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
        from app.feature.airlines.airline_service import get_airline_statistics
        
        airline_stats_map = {}
        for code in airline_codes:
            # 병렬 처리하면 좋겠지만, 일단 순차 처리 (캐싱 고려 가능)
            try:
                stats = await get_airline_statistics(code)
                if stats:
                    airline_stats_map[code] = stats
            except Exception:
                # 개별 항공사 조회 실패해도 전체 로직은 진행
                continue
        
        # 4. 결과에 항공사 정보 주입
        for offer in flight_offers:
            if offer.validating_airline_codes:
                code = offer.validating_airline_codes[0]
                if code in airline_stats_map:
                    offer.airline_info = airline_stats_map[code]
        
        # 5. 정렬 (요청된 경우)
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

        return FlightSearchResponse(
            flight_offers=flight_offers,
            count=len(flight_offers),
        )

    except ExternalApiError:
        raise
    except Exception as e:
        raise ExternalApiError(
            provider="Amadeus",
            detail=f"항공편 검색 중 오류가 발생했습니다: {str(e)}",
        ) from e


async def _search_local_airports(keyword: str) -> List[LocationSchema]:
    """
    Firestore 'airports' 컬렉션에서 한글/영어/코드 기반 부분 검색.
    """
    keyword_lower = keyword.lower()

    def _fetch():
        return list(airports_collection.stream())

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


async def search_locations(keyword: str) -> LocationSearchResponse:
    """
    키워드를 기반으로 공항 및 도시를 검색합니다.
    1) 로컬 Firestore 'airports' 컬렉션 우선 검색 (오프라인/캐시된 추천)
    2) Amadeus API 검색 결과를 병합 (중복 IATA 제거)
    """
    try:
        combined: List[LocationSchema] = []
        seen_codes = set()

        # 1) 로컬 검색
        local_locations = await _search_local_airports(keyword)
        for loc in local_locations:
            if loc.iata_code not in seen_codes:
                seen_codes.add(loc.iata_code)
                combined.append(loc)

        # 2) Amadeus API 호출 (보조)
        locations_data = await amadeus_client.search_locations(
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

