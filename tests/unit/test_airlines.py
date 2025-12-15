"""
항공사 서비스 단위 테스트
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from app.feature.airlines.airline_service import AirlineService
from app.feature.airlines.models import Airline
from app.core.exceptions.exceptions import DatabaseError


@pytest.fixture
def mock_firebase_service():
    """Firebase 서비스 모킹"""
    service = MagicMock()
    service.db.collection.return_value = MagicMock()
    return service


@pytest.fixture
def airline_service(mock_firebase_service):
    """AirlineService 인스턴스 생성"""
    # 전역 TTL 캐시가 테스트 간에 영향을 주지 않도록 초기화
    import app.feature.airlines.airline_service as airline_service_module
    airline_service_module._AIRLINES_SORTED_TOP10_CACHE.clear()
    airline_service_module._AIRLINES_ALL_CACHE.clear()
    return AirlineService(firebase_service=mock_firebase_service)


class TestSearchAirlines:
    """항공사 검색 기능 테스트"""

    @pytest.mark.asyncio
    async def test_search_airlines_success(self, airline_service):
        """항공사 검색 성공"""
        # Arrange
        mock_doc = MagicMock()
        mock_doc.id = "KE"
        mock_doc.to_dict.return_value = {
            "airlineName":"대한항공",
            "country": "대한민국",
            "alliance": "SkyTeam",
            "type": "FSC",
            "averageRatings": {"overall": 4.5},
            "totalReviews": 100,
            "logoUrl": "https://example.com/ke.png"
        }
        
        with patch("app.feature.airlines.airline_service.run_in_threadpool") as mock_thread:
            mock_thread.return_value = [mock_doc]
            
            # Act
            results = await airline_service.search_airlines("대한")
            
            # Assert
            assert len(results) == 1
            assert results[0].code == "KE"
            assert results[0].name == "대한항공"
            assert results[0].rating == 4.5

    @pytest.mark.asyncio
    async def test_search_airlines_empty_query(self, airline_service):
        """빈 검색어로 검색"""
        results = await airline_service.search_airlines("")
        assert results == []

    @pytest.mark.asyncio
    async def test_search_airlines_database_error(self, airline_service):
        """데이터베이스 오류 처리"""
        with patch("app.feature.airlines.airline_service.run_in_threadpool") as mock_thread:
            mock_thread.side_effect = Exception("DB Connection Error")
            
            with pytest.raises(DatabaseError) as exc_info:
                await airline_service.search_airlines("대한")
            
            assert "항공사 검색 중 오류 발생" in str(exc_info.value.message)


class TestGetPopularAirlines:
    """인기 항공사 조회 테스트"""

    @pytest.mark.asyncio
    async def test_get_popular_airlines_success(self, airline_service):
        """인기 항공사 조회 성공"""
        # Arrange
        mock_docs = []
        for code, name, rating, reviews in [
            ("KE", "대한항공", 4.5, 100),
            ("OZ", "아시아나항공", 4.3, 80),
            ("7C", "제주항공", 4.0, 50),
        ]:
            mock_doc = MagicMock()
            mock_doc.id = code
            mock_doc.to_dict.return_value = {
                "airlineName": name,
                "country": "대한민국",
                "averageRatings": {"overall": rating},
                "totalReviews": reviews,
            }
            mock_docs.append(mock_doc)
        
        with patch("app.feature.airlines.airline_service.run_in_threadpool") as mock_thread:
            mock_thread.return_value = mock_docs
            
            # Act
            results = await airline_service.get_popular_airlines(limit=3)
            
            # Assert
            assert len(results) == 3
            assert results[0].rank == 1
            assert results[1].rank == 2
            assert results[2].rank == 3
            # 가중 평점 순으로 정렬되어야 함
            assert results[0].code == "KE"

    @pytest.mark.asyncio
    async def test_get_popular_airlines_database_error(self, airline_service):
        """데이터베이스 오류 처리"""
        with patch("app.feature.airlines.airline_service.run_in_threadpool") as mock_thread:
            mock_thread.side_effect = Exception("DB Connection Error")
            
            with pytest.raises(DatabaseError) as exc_info:
                await airline_service.get_popular_airlines()
            
            assert "인기 항공사 조회 중 오류 발생" in str(exc_info.value.message)


class TestGetPopularAirlinesWeekly:
    """주간 인기 항공사 조회 테스트"""

    @pytest.mark.asyncio
    async def test_get_popular_airlines_weekly_success(self, airline_service):
        """주간 인기 항공사 조회 성공"""
        # Arrange
        mock_review_docs = []
        for i in range(5):
            mock_doc = MagicMock()
            mock_doc.to_dict.return_value = {
                "airlineCode": "KE",
                "overallRating": 4.5,
                "createdAt": datetime.now(timezone.utc),
            }
            mock_review_docs.append(mock_doc)
        
        mock_airline_doc = MagicMock()
        mock_airline_doc.exists = True
        mock_airline_doc.to_dict.return_value = {
            "airlineName": "대한항공",
            "country": "대한민국",
            "logoUrl": "https://example.com/ke.png"
        }
        
        with patch("app.feature.airlines.airline_service.run_in_threadpool") as mock_thread:
            mock_thread.side_effect = [
                mock_review_docs,
                {"KE": mock_airline_doc}
            ]
            
            # Act
            results = await airline_service.get_popular_airlines_weekly(2025, 12, 2, limit=5)
            
            # Assert
            assert len(results) <= 5
            if results:
                assert results[0].rank == 1

    @pytest.mark.asyncio
    async def test_get_popular_airlines_weekly_no_reviews(self, airline_service):
        """리뷰가 없는 경우"""
        with patch("app.feature.airlines.airline_service.run_in_threadpool") as mock_thread:
            mock_thread.return_value = []
            
            results = await airline_service.get_popular_airlines_weekly(2025, 12, 2)
            assert results == []

    @pytest.mark.asyncio
    async def test_get_popular_airlines_weekly_invalid_week(self, airline_service):
        """잘못된 주차 입력"""
        with pytest.raises(ValueError) as exc_info:
            await airline_service.get_popular_airlines_weekly(2025, 12, 0)
        
        assert "week는 1 이상" in str(exc_info.value)


class TestGetAirlineStatistics:
    """항공사 통계 조회 테스트"""

    @pytest.mark.asyncio
    async def test_get_airline_statistics_success(self, airline_service):
        """항공사 통계 조회 성공"""
        # Arrange
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "airlineName": "대한항공",
            "country": "대한민국",
            "averageRatings": {
                "service": 4.5,
                "comfort": 4.3,
                "food": 4.0
            },
            "totalReviews": 100,
        }
        
        with patch("app.feature.airlines.airline_service.run_in_threadpool") as mock_thread:
            mock_thread.return_value = mock_doc
            
            # Act
            result = await airline_service.get_airline_statistics("KE")
            
            # Assert
            assert result is not None
            assert result.airlineName == "대한항공"
            assert "overallRating" in result.dict()

    @pytest.mark.asyncio
    async def test_get_airline_statistics_not_found(self, airline_service):
        """존재하지 않는 항공사"""
        mock_doc = MagicMock()
        mock_doc.exists = False
        
        with patch("app.feature.airlines.airline_service.run_in_threadpool") as mock_thread:
            mock_thread.return_value = mock_doc
            
            result = await airline_service.get_airline_statistics("INVALID")
            assert result is None

    @pytest.mark.asyncio
    async def test_get_airline_statistics_database_error(self, airline_service):
        """데이터베이스 오류 처리"""
        with patch("app.feature.airlines.airline_service.run_in_threadpool") as mock_thread:
            mock_thread.side_effect = Exception("DB Connection Error")
            
            with pytest.raises(DatabaseError) as exc_info:
                await airline_service.get_airline_statistics("KE")
            
            assert "항공사 통계 조회 중 오류 발생" in str(exc_info.value.message)
