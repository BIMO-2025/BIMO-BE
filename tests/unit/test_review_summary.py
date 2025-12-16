import pytest
from unittest.mock import AsyncMock, MagicMock
from app.feature.reviews.review_summary_service import ReviewSummaryService
from app.feature.reviews.reviews_schemas import ReviewSchema, BIMOSummaryResponse
from app.feature.llm.llm_service import LLMService

@pytest.fixture
def mock_llm_service():
    return AsyncMock(spec=LLMService)

@pytest.fixture
def summary_service(mock_llm_service):
    return ReviewSummaryService(llm_service=mock_llm_service)

@pytest.fixture
def sample_reviews():
    ratings = {
        "seatComfort": 5, "inflightMeal": 5, "service": 5, "cleanliness": 5, "checkIn": 5
    }
    return [
        ReviewSchema(
            id="1", userId="u1", userNickname="User1", airlineCode="KE", airlineName="KA", 
            route="Incheon-Paris", overallRating=5, ratings=ratings, text="Good food"
        ),
        ReviewSchema(
            id="2", userId="u2", userNickname="User2", airlineCode="KE", airlineName="KA", 
            route="Incheon-Paris", overallRating=2, ratings=ratings, text="Bad service"
        ),
    ]

@pytest.mark.asyncio
async def test_generate_bimo_summary(summary_service, mock_llm_service, sample_reviews):
    # Mock LLM response with Markdown block
    mock_llm_service.generate_chat_completion.return_value = """
    ```json
    {
        "good_points": ["Delicious meal", "Comfortable seat"],
        "bad_points": ["Unkind crew"]
    }
    ```
    """

    result = await summary_service.generate_bimo_summary(sample_reviews, "KE", "Korean Air")

    assert isinstance(result, BIMOSummaryResponse)
    assert result.airline_code == "KE"
    assert len(result.good_points) == 2
    assert "Delicious meal" in result.good_points
    assert len(result.bad_points) == 1
    assert result.review_count == 2
    
    # LLM 호출 검증
    mock_llm_service.generate_chat_completion.assert_called_once()

@pytest.mark.asyncio
async def test_generate_bimo_summary_empty(summary_service):
    result = await summary_service.generate_bimo_summary([], "KE", "Korean Air")
    assert result.review_count == 0
    assert result.good_points == []

@pytest.mark.asyncio
async def test_generate_bimo_summary_parsing_error(summary_service, mock_llm_service, sample_reviews):
    # Mock invalid JSON response
    mock_llm_service.generate_chat_completion.return_value = "Invalid JSON"

    result = await summary_service.generate_bimo_summary(sample_reviews, "KE", "Korean Air")

    # Should handle error gracefully and return empty points
    assert result.good_points == []
    assert result.bad_points == []
    assert result.review_count == 2

@pytest.mark.asyncio
async def test_summarize_reviews_text(summary_service, mock_llm_service, sample_reviews):
    mock_llm_service.generate_chat_completion.return_value = "Summary text"
    
    summary = await summary_service.summarize_reviews_text(sample_reviews, "Korean Air")
    
    assert summary == "Summary text"
    mock_llm_service.generate_chat_completion.assert_called_once()
