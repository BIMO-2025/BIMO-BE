"""
리뷰 모듈 단위 테스트
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone

from app.feature.reviews import reviews_service
from app.feature.reviews.reviews_schemas import ReviewSchema, RatingsSchema
from app.core.exceptions.exceptions import ReviewNotFoundError, DatabaseError


class TestReviewsService:
    """reviews_service 모듈 테스트"""

    @pytest.mark.asyncio
    async def test_get_reviews_by_airline_success(self, mock_firebase_db):
        """항공사별 리뷰 조회 성공"""
        # Firestore 문서 모킹
        mock_doc1 = Mock()
        mock_doc1.id = "review-1"
        mock_doc1.to_dict.return_value = {
            "userId": "user-1",
            "airlineCode": "KE",
            "airlineName": "대한항공",
            "text": "좋은 항공사",
            "overallRating": 4.5,
            "ratings": {
                "seatComfort": 4.0,
                "inflightMeal": 4.5,
                "service": 5.0,
                "cleanliness": 4.0,
                "checkIn": 4.5
            },
            "createdAt": datetime.now(timezone.utc).isoformat()
        }
        
        mock_doc2 = Mock()
        mock_doc2.id = "review-2"
        mock_doc2.to_dict.return_value = {
            "userId": "user-2",
            "airlineCode": "KE",
            "airlineName": "대한항공",
            "text": "매우 만족",
            "overallRating": 5.0,
            "ratings": {
                "seatComfort": 5.0,
                "inflightMeal": 5.0,
                "service": 5.0,
                "cleanliness": 5.0,
                "checkIn": 5.0
            },
            "createdAt": datetime.now(timezone.utc).isoformat()
        }
        
        mock_query = Mock()
        mock_query.stream.return_value = [mock_doc1, mock_doc2]
        mock_query.limit.return_value = mock_query
        
        mock_collection = Mock()
        mock_collection.where.return_value = mock_query
        
        with patch("app.feature.reviews.reviews_service.reviews_collection", mock_collection):
            reviews = await reviews_service.get_reviews_by_airline("KE", limit=10)
            
            assert len(reviews) == 2
            assert reviews[0].airlineCode == "KE"
            assert reviews[0].overallRating == 4.5

    @pytest.mark.asyncio
    async def test_get_reviews_by_airline_empty(self, mock_firebase_db):
        """항공사별 리뷰 없음"""
        mock_query = Mock()
        mock_query.stream.return_value = []
        mock_query.limit.return_value = mock_query
        
        mock_collection = Mock()
        mock_collection.where.return_value = mock_query
        
        with patch("app.feature.reviews.reviews_service.reviews_collection", mock_collection):
            reviews = await reviews_service.get_reviews_by_airline("KE", limit=10)
            
            assert len(reviews) == 0

    @pytest.mark.asyncio
    async def test_get_review_by_id_success(self, mock_firebase_db):
        """리뷰 ID로 조회 성공"""
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "userId": "user-1",
            "airlineCode": "KE",
            "airlineName": "대한항공",
            "text": "좋은 항공사",
            "overallRating": 4.5,
            "ratings": {
                "seatComfort": 4.0,
                "inflightMeal": 4.5,
                "service": 5.0,
                "cleanliness": 4.0,
                "checkIn": 4.5
            },
            "createdAt": datetime.now(timezone.utc).isoformat()
        }
        
        mock_ref = Mock()
        mock_ref.get = Mock(return_value=mock_doc)
        
        mock_collection = Mock()
        mock_collection.document.return_value = mock_ref
        
        with patch("app.feature.reviews.reviews_service.reviews_collection", mock_collection):
            review = await reviews_service.get_review_by_id("review-123")
            
            assert review.airlineCode == "KE"
            assert review.overallRating == 4.5

    @pytest.mark.asyncio
    async def test_get_review_by_id_not_found(self, mock_firebase_db):
        """리뷰를 찾을 수 없음"""
        mock_doc = Mock()
        mock_doc.exists = False
        
        mock_ref = Mock()
        mock_ref.get = Mock(return_value=mock_doc)
        
        mock_collection = Mock()
        mock_collection.document.return_value = mock_ref
        
        with patch("app.feature.reviews.reviews_service.reviews_collection", mock_collection):
            with pytest.raises(ReviewNotFoundError):
                await reviews_service.get_review_by_id("non-existent-review")

    @pytest.mark.asyncio
    async def test_summarize_reviews_no_reviews(self):
        """리뷰가 없을 때 요약"""
        with patch.object(reviews_service, "get_reviews_by_airline", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = []
            
            summary = await reviews_service.summarize_reviews("KE", "대한항공")
            
            assert "리뷰가 아직 없습니다" in summary

    @pytest.mark.asyncio
    async def test_summarize_reviews_with_reviews(self):
        """리뷰가 있을 때 요약"""
        from app.feature.reviews.reviews_schemas import ReviewSchema, RatingsSchema
        
        reviews = [
            ReviewSchema(
                id="review-1",
                userId="user-1",
                airlineCode="KE",
                airlineName="대한항공",
                text="좋은 항공사입니다",
                overallRating=4.5,
                ratings=RatingsSchema(
                    seatComfort=4.0,
                    inflightMeal=4.5,
                    service=5.0,
                    cleanliness=4.0,
                    checkIn=4.5
                ),
                createdAt=datetime.now(timezone.utc)
            )
        ]
        
        with patch.object(reviews_service, "get_reviews_by_airline", new_callable=AsyncMock) as mock_get, \
             patch.object(reviews_service, "llm_service") as mock_llm:
            
            mock_get.return_value = reviews
            mock_llm.generate_chat_completion = AsyncMock(return_value="요약된 리뷰 내용")
            
            summary = await reviews_service.summarize_reviews("KE", "대한항공")
            
            assert summary == "요약된 리뷰 내용"
            mock_llm.generate_chat_completion.assert_called_once()

