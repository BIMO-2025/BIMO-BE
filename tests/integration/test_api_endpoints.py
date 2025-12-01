"""
API 엔드포인트 통합 테스트
"""
import pytest
from unittest.mock import AsyncMock, patch, Mock
from datetime import datetime, timezone, timedelta

from app.shared.schemas import UserInDB


class TestRootEndpoint:
    """루트 엔드포인트 테스트"""

    def test_read_root(self, client):
        """루트 엔드포인트 테스트"""
        response = client.get("/")
        
        assert response.status_code == 200
        assert response.json() == {"Hello": "Welcome to BIMO-BE API"}


class TestAuthEndpoints:
    """인증 엔드포인트 통합 테스트"""

    @pytest.mark.asyncio
    async def test_google_login_success(self, client, sample_firebase_token):
        """Google 로그인 성공"""
        with patch("app.feature.auth.auth_service.authenticate_with_google", new_callable=AsyncMock) as mock_auth:
            mock_user = UserInDB(
                uid="test-user-123",
                email="test@example.com",
                display_name="Test User",
                photo_url="https://example.com/photo.jpg",
                provider_id="google.com",
                created_at=datetime.now(timezone.utc),
                last_login_at=datetime.now(timezone.utc)
            )
            
            mock_auth.return_value = {
                "access_token": "test-jwt-token",
                "token_type": "bearer",
                "user": mock_user
            }
            
            response = client.post(
                "/auth/google/login",
                json={"token": "firebase-id-token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_apple_login_success(self, client, sample_firebase_token):
        """Apple 로그인 성공"""
        with patch("app.feature.auth.auth_service.authenticate_with_apple", new_callable=AsyncMock) as mock_auth:
            mock_user = UserInDB(
                uid="test-user-123",
                email="test@example.com",
                display_name="Test User",
                photo_url="https://example.com/photo.jpg",
                provider_id="apple.com",
                created_at=datetime.now(timezone.utc),
                last_login_at=datetime.now(timezone.utc)
            )
            
            mock_auth.return_value = {
                "access_token": "test-jwt-token",
                "token_type": "bearer",
                "user": mock_user
            }
            
            response = client.post(
                "/auth/apple/login",
                json={"token": "firebase-id-token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data

    @pytest.mark.asyncio
    async def test_kakao_login_success(self, client):
        """Kakao 로그인 성공"""
        with patch("app.feature.auth.auth_service.authenticate_with_kakao", new_callable=AsyncMock) as mock_auth:
            mock_user = UserInDB(
                uid="test-user-123",
                email="test@example.com",
                display_name="Test User",
                photo_url="https://example.com/photo.jpg",
                provider_id="kakao.com",
                created_at=datetime.now(timezone.utc),
                last_login_at=datetime.now(timezone.utc)
            )
            
            mock_auth.return_value = {
                "access_token": "test-jwt-token",
                "token_type": "bearer",
                "user": mock_user
            }
            
            response = client.post(
                "/auth/kakao/login",
                json={"token": "kakao-access-token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data

    def test_auth_login_missing_token(self, client):
        """토큰이 없는 경우"""
        response = client.post(
            "/auth/google/login",
            json={}
        )
        
        assert response.status_code == 422  # Validation error


class TestReviewsEndpoints:
    """리뷰 엔드포인트 통합 테스트"""

    @pytest.mark.asyncio
    async def test_get_reviews_by_airline(self, client, mock_firebase_db):
        """항공사별 리뷰 조회"""
        with patch("app.feature.reviews.reviews_service.get_reviews_by_airline", new_callable=AsyncMock) as mock_get:
            from app.feature.reviews.reviews_schemas import ReviewSchema, RatingsSchema
            
            mock_reviews = [
                ReviewSchema(
                    id="review-1",
                    userId="user-1",
                    userNickname="User1",
                    airlineCode="KE",
                    airlineName="대한항공",
                    route="ICN-JFK",
                    text="좋은 항공사",
                    overallRating=4.5,
                    ratings=RatingsSchema(
                        seatComfort=4,
                        inflightMeal=4,
                        service=5,
                        cleanliness=4,
                        checkIn=4
                    ),
                    createdAt=datetime.now(timezone.utc)
                )
            ]
            
            mock_get.return_value = mock_reviews
            
            response = client.get("/reviews/airline/KE")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            if len(data) > 0:
                assert data[0]["airlineCode"] == "KE"

    @pytest.mark.asyncio
    async def test_get_review_by_id(self, client):
        """리뷰 ID로 조회"""
        with patch("app.feature.reviews.reviews_service.get_review_by_id", new_callable=AsyncMock) as mock_get:
            from app.feature.reviews.reviews_schemas import ReviewSchema, RatingsSchema
            
            mock_review = ReviewSchema(
                id="review-123",
                userId="user-1",
                userNickname="User1",
                airlineCode="KE",
                airlineName="대한항공",
                route="ICN-JFK",
                text="좋은 항공사",
                overallRating=4.5,
                ratings=RatingsSchema(
                    seatComfort=4,
                    inflightMeal=4,
                    service=5,
                    cleanliness=4,
                    checkIn=4
                ),
                createdAt=datetime.now(timezone.utc)
            )
            
            mock_get.return_value = mock_review
            
            response = client.get("/reviews/review-123")
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "review-123"


class TestWellnessEndpoints:
    """시차적응 엔드포인트 통합 테스트"""

    @pytest.mark.asyncio
    async def test_generate_jetlag_plan(self, client):
        """시차적응 계획 생성"""
        with patch("app.feature.wellness.wellness_service.generate_jetlag_plan", new_callable=AsyncMock) as mock_generate:
            from app.feature.wellness.wellness_schemas import JetLagPlanResponse, DailySchedule, FlightSegment
            
            base_time = datetime.now()
            
            mock_response = JetLagPlanResponse(
                daily_schedules=[
                    DailySchedule(
                        date=base_time.date().isoformat(),
                        recommendations=["충분한 수면", "가벼운 운동"],
                        activities=["휴식"],
                        notes="메모",
                        day_number=1,
                        local_timezone="America/New_York",
                        sleep_window="22:00-07:00",
                        meal_times=["08:00", "13:00", "19:00"]
                    )
                ],
                summary="시차적응 계획 요약",
                general_recommendations=["물 많이 마시기"],
                pre_flight_tips=["충분한 휴식"],
                post_arrival_tips=["햇빛 쐬기"],
                algorithm_explanation="알고리즘 설명",
                origin_timezone="Asia/Seoul",
                destination_timezone="America/New_York",
                time_difference_hours=14,
                total_flight_duration_hours=14
            )
            
            mock_generate.return_value = mock_response
            
            request_data = {
                "origin_timezone": "Asia/Seoul",
                "destination_timezone": "America/New_York",
                "flight_segments": [
                    {
                        "departure_airport": "ICN",
                        "arrival_airport": "JFK",
                        "departure_time": base_time.isoformat(),
                        "arrival_time": (base_time + timedelta(hours=14)).isoformat()
                    }
                ],
                "trip_duration_days": 7
            }
            
            response = client.post(
                "/wellness/jetlag-plan",
                json=request_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "daily_schedules" in data or "summary" in data


class TestLLMEndpoints:
    """LLM 엔드포인트 통합 테스트"""

    @pytest.mark.asyncio
    async def test_llm_chat(self, client, mock_gemini_client):
        """LLM 채팅 테스트"""
        with patch("app.feature.llm.llm_service.generate_chat_completion", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = "LLM 응답 텍스트"
            
            request_data = {
                "prompt": "테스트 질문"
            }
            
            response = client.post(
                "/llm/chat",
                json=request_data
            )
            
            assert response.status_code == 200
            data = response.json()
            assert response.status_code == 200
            data = response.json()
            assert "content" in data or "response" in data or "text" in data or isinstance(data, str)


class TestErrorHandling:
    """에러 처리 테스트"""

    def test_not_found_endpoint(self, client):
        """존재하지 않는 엔드포인트"""
        response = client.get("/non-existent-endpoint")
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_invalid_request_body(self, client):
        """잘못된 요청 본문"""
        response = client.post(
            "/auth/google/login",
            json={"invalid": "data"}
        )
        
        # 토큰이 없으면 422 (Validation Error)
        assert response.status_code in [400, 422]

