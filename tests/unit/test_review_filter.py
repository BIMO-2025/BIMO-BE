import pytest
from datetime import datetime, timedelta, timezone
from app.feature.reviews.review_filter_service import ReviewFilterService
from app.feature.reviews.reviews_schemas import ReviewSchema, ReviewFilterRequest

@pytest.fixture
def filter_service():
    return ReviewFilterService()

@pytest.fixture
def sample_reviews():
    now = datetime.now(timezone.utc)
    ratings = {
        "seatComfort": 5, "inflightMeal": 5, "service": 5, "cleanliness": 5, "checkIn": 5
    }
    return [
        ReviewSchema(
            id="1",
            userId="u1",
            userNickname="User1",
            airlineCode="KE",
            airlineName="Korean Air",
            route="ICN-LAX",
            seatClass="Economy",
            overallRating=5,
            ratings=ratings,
            createdAt=now,
            likes=10,
            text="Excellent",
            imageUrls=["http://example.com/img1.jpg"]
        ),
        ReviewSchema(
            id="2",
            userId="u2",
            userNickname="User2",
            airlineCode="KE",
            airlineName="Korean Air",
            route="ICN-CDG",
            seatClass="Prestige",
            overallRating=4,
            ratings=ratings,
            createdAt=now - timedelta(days=100),
            likes=5,
            text="Good",
            imageUrls=[]
        ),
        ReviewSchema(
            id="3",
            userId="u3",
            userNickname="User3",
            airlineCode="KE",
            airlineName="Korean Air",
            route="JFK-ICN",
            seatClass="First",
            overallRating=2,
            ratings=ratings,
            createdAt=now - timedelta(days=200),
            likes=0,
            text="Bad",
            imageUrls=[]
        ),
    ]

def test_filter_reviews_route(filter_service, sample_reviews):
    # ICN 도착 필터
    req = ReviewFilterRequest(arrival_airport="LAX")
    result = filter_service.filter_reviews(sample_reviews, req)
    assert len(result) == 1
    assert result[0].id == "1"

    # ICN 출발 필터
    req = ReviewFilterRequest(departure_airport="ICN")
    result = filter_service.filter_reviews(sample_reviews, req)
    assert len(result) == 2  # 1, 2

def test_filter_reviews_seat_class(filter_service, sample_reviews):
    # 이코노미 필터
    req = ReviewFilterRequest(seat_class="이코노미")
    result = filter_service.filter_reviews(sample_reviews, req)
    assert len(result) == 1
    assert result[0].seatClass == "Economy"

    # 비즈니스 필터 (Prestige 포함)
    req = ReviewFilterRequest(seat_class="비즈니스")
    result = filter_service.filter_reviews(sample_reviews, req)
    assert len(result) == 1
    assert result[0].seatClass == "Prestige"

def test_filter_reviews_period(filter_service, sample_reviews):
    # 최근 3개월 (90일)
    req = ReviewFilterRequest(period="최근 3개월")
    result = filter_service.filter_reviews(sample_reviews, req)
    assert len(result) == 1  # 1 (오늘)
    
    # 최근 6개월 (180일)
    req = ReviewFilterRequest(period="최근 6개월")
    result = filter_service.filter_reviews(sample_reviews, req)
    assert len(result) == 2  # 1 (오늘), 2 (100일 전)

def test_filter_reviews_rating(filter_service, sample_reviews):
    # 평점 4점 이상
    req = ReviewFilterRequest(min_rating=4)
    result = filter_service.filter_reviews(sample_reviews, req)
    assert len(result) == 2  # 1 (5점), 2 (4점)

def test_filter_reviews_photo_only(filter_service, sample_reviews):
    req = ReviewFilterRequest(photo_only=True)
    result = filter_service.filter_reviews(sample_reviews, req)
    assert len(result) == 1
    assert result[0].id == "1"

def test_sort_reviews(filter_service, sample_reviews):
    # 평점 높은 순
    sorted_reviews = filter_service.sort_reviews(sample_reviews, "rating_high")
    assert sorted_reviews[0].id == "1"  # 5점
    assert sorted_reviews[1].id == "2"  # 4점
    assert sorted_reviews[2].id == "3"  # 2점

    # 좋아요 많은 순
    sorted_reviews = filter_service.sort_reviews(sample_reviews, "likes_high")
    assert sorted_reviews[0].id == "1"  # 10개
    assert sorted_reviews[1].id == "2"  # 5개

def test_paginate_reviews(filter_service, sample_reviews):
    limit = 2
    offset = 0
    paged, has_more = filter_service.paginate_reviews(sample_reviews, limit, offset)
    assert len(paged) == 2
    assert has_more is True
    
    offset = 2
    paged, has_more = filter_service.paginate_reviews(sample_reviews, limit, offset)
    assert len(paged) == 1
    assert has_more is False
