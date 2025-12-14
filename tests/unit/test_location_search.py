"""
위치 검색 기능 단위 테스트
"""
import pytest
from unittest.mock import MagicMock, patch

from app.feature.flights.flights_service import FlightsService
from app.feature.flights.flights_schemas import LocationSearchResponse
from app.core.exceptions.exceptions import ExternalApiError


@pytest.fixture
def mock_firebase_service():
    """Firebase 서비스 모킹"""
    service = MagicMock()
    service.db.collection.return_value = MagicMock()
    return service


@pytest.fixture
def mock_amadeus_client():
    """Amadeus 클라이언트 모킹"""
    return MagicMock()


@pytest.fixture
def flights_service(mock_amadeus_client, mock_firebase_service):
    """FlightsService 인스턴스 생성"""
    return FlightsService(
        amadeus_client=mock_amadeus_client,
        firebase_service=mock_firebase_service
    )


class TestSearchLocations:
    """위치 검색 기능 테스트"""

    @pytest.mark.asyncio
    async def test_search_locations_local_only(self, flights_service):
        """로컬 데이터만 있는 경우"""
        # Arrange
        mock_doc = MagicMock()
        mock_doc.to_dict.return_value = {
            "code": "ICN",
            "name": "인천국제공항",
            "name_en": "Incheon International Airport",
            "name_ko": "인천국제공항",
            "city": "Seoul",
            "city_en": "Seoul",
            "city_ko": "서울",
            "country": "South Korea",
            "country_en": "South Korea",
            "country_ko": "대한민국",
        }
        
        with patch("app.feature.flights.flights_service.run_in_threadpool") as mock_thread:
            mock_thread.return_value = [mock_doc]
            
            flights_service.amadeus_client.search_locations = MagicMock(return_value=[])
            
            # Act
            result = await flights_service.search_locations("인천")
            
            # Assert
            assert result.count == 1
            assert result.locations[0].iata_code == "ICN"
            assert result.locations[0].sub_type == "AIRPORT"

    @pytest.mark.asyncio
    async def test_search_locations_amadeus_merge(self, flights_service):
        """로컬 + Amadeus API 결과 병합"""
        # Arrange: 로컬 결과
        mock_local_doc = MagicMock()
        mock_local_doc.to_dict.return_value = {
            "code": "ICN",
            "name": "인천국제공항",
            "city_ko": "서울",
            "country_ko": "대한민국",
        }
        
        # Amadeus API 결과 (다른 공항)
        amadeus_result = [{
            "id": "JFK",
            "name": "John F. Kennedy International Airport",
            "iataCode": "JFK",
            "geoCode": {"latitude": 40.6413, "longitude": -73.7781},
            "address": {"cityName": "New York", "countryName": "United States"},
            "subType": "AIRPORT"
        }]
        
        with patch("app.feature.flights.flights_service.run_in_threadpool") as mock_thread:
            mock_thread.return_value = [mock_local_doc]
            
            flights_service.amadeus_client.search_locations = MagicMock(return_value=amadeus_result)
            
            # Act
            result = await flights_service.search_locations("airport")
            
            # Assert
            assert result.count == 2  # ICN + JFK
            codes = [loc.iata_code for loc in result.locations]
            assert "ICN" in codes
            assert "JFK" in codes

    @pytest.mark.asyncio
    async def test_search_locations_duplicate_removal(self, flights_service):
        """중복 IATA 코드 제거 확인"""
        # Arrange: 로컬 결과에 ICN
        mock_local_doc = MagicMock()
        mock_local_doc.to_dict.return_value = {
            "code": "ICN",
            "name": "인천국제공항",
            "city_ko": "서울",
            "country_ko": "대한민국",
        }
        
        # Amadeus 결과에도 ICN (중복)
        amadeus_result = [{
            "id": "ICN",
            "name": "Incheon International Airport",
            "iataCode": "ICN",
            "address": {"cityName": "Seoul", "countryName": "South Korea"},
            "subType": "AIRPORT"
        }]
        
        with patch("app.feature.flights.flights_service.run_in_threadpool") as mock_thread:
            mock_thread.return_value = [mock_local_doc]
            
            flights_service.amadeus_client.search_locations = MagicMock(return_value=amadeus_result)
            
            # Act
            result = await flights_service.search_locations("인천")
            
            # Assert
            assert result.count == 1  # 중복 제거됨
            assert result.locations[0].iata_code == "ICN"

    @pytest.mark.asyncio
    async def test_search_locations_city_support(self, flights_service):
        """도시 검색 지원 확인"""
        amadeus_result = [{
            "id": "CNYC",
            "name": "New York",
            "detailed_name": "New York, United States",
            "iataCode": "NYC",
            "address": {"cityName": "New York", "countryName": "United States"},
            "subType": "CITY"
        }]
        
        with patch("app.feature.flights.flights_service.run_in_threadpool") as mock_thread:
            mock_thread.return_value = []
            
            flights_service.amadeus_client.search_locations = MagicMock(return_value=amadeus_result)
            
            # Act
            result = await flights_service.search_locations("New York")
            
            # Assert
            assert result.count == 1
            assert result.locations[0].sub_type == "CITY"

    @pytest.mark.asyncio
    async def test_search_locations_amadeus_api_error(self, flights_service):
        """Amadeus API 오류 처리"""
        with patch("app.feature.flights.flights_service.run_in_threadpool") as mock_thread:
            mock_thread.return_value = []
            
            flights_service.amadeus_client.search_locations = MagicMock(
                side_effect=Exception("Amadeus API Error")
            )
            
            with pytest.raises(ExternalApiError) as exc_info:
                await flights_service.search_locations("test")
            
            assert "위치 검색 중 오류가 발생했습니다" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_search_locations_empty_keyword(self, flights_service):
        """빈 검색어 처리"""
        with patch("app.feature.flights.flights_service.run_in_threadpool") as mock_thread:
            mock_thread.return_value = []
            
            flights_service.amadeus_client.search_locations = MagicMock(return_value=[])
            
            result = await flights_service.search_locations("")
            
            assert isinstance(result, LocationSearchResponse)
            assert result.count >= 0


class TestSearchLocalAirports:
    """로컬 공항 검색 기능 테스트"""

    @pytest.mark.asyncio
    async def test_search_local_airports_korean(self, flights_service):
        """한글 검색"""
        mock_doc = MagicMock()
        mock_doc.to_dict.return_value = {
            "code": "GMP",
            "name": "김포국제공항",
            "name_ko": "김포국제공항",
            "city_ko": "서울",
            "country_ko": "대한민국",
        }
        
        with patch("app.feature.flights.flights_service.run_in_threadpool") as mock_thread:
            mock_thread.return_value = [mock_doc]
            
            result = await flights_service._search_local_airports("김포")
            
            assert len(result) == 1
            assert result[0].iata_code == "GMP"

    @pytest.mark.asyncio
    async def test_search_local_airports_english(self, flights_service):
        """영어 검색"""
        mock_doc = MagicMock()
        mock_doc.to_dict.return_value = {
            "code": "GMP",
            "name": "Gimpo International Airport",
            "name_en": "Gimpo International Airport",
            "city_en": "Seoul",
            "country_en": "South Korea",
        }
        
        with patch("app.feature.flights.flights_service.run_in_threadpool") as mock_thread:
            mock_thread.return_value = [mock_doc]
            
            result = await flights_service._search_local_airports("gimpo")
            
            assert len(result) == 1
            assert result[0].iata_code == "GMP"

    @pytest.mark.asyncio
    async def test_search_local_airports_iata_code(self, flights_service):
        """IATA 코드로 검색"""
        mock_doc = MagicMock()
        mock_doc.to_dict.return_value = {
            "code": "ICN",
            "name": "인천국제공항",
            "city_ko": "서울",
            "country_ko": "대한민국",
        }
        
        with patch("app.feature.flights.flights_service.run_in_threadpool") as mock_thread:
            mock_thread.return_value = [mock_doc]
            
            result = await flights_service._search_local_airports("ICN")
            
            assert len(result) == 1
            assert result[0].iata_code == "ICN"

    @pytest.mark.asyncio
    async def test_search_local_airports_case_insensitive(self, flights_service):
        """대소문자 구분 없이 검색"""
        mock_doc = MagicMock()
        mock_doc.to_dict.return_value = {
            "code": "ICN",
            "name": "Incheon International Airport",
            "name_en": "Incheon International Airport",
        }
        
        with patch("app.feature.flights.flights_service.run_in_threadpool") as mock_thread:
            mock_thread.return_value = [mock_doc]
            
            result = await flights_service._search_local_airports("incheon")
            
            assert len(result) == 1
