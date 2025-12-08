import uuid
from datetime import datetime
from typing import List
from app.core.firebase import db
from app.feature.reviews.models import Review, ReviewCreate

class ReviewService:
    def __init__(self):
        self.collection = db.collection("reviews")

    async def create_review(self, user_id: str, review_data: ReviewCreate) -> Review:
        review_id = str(uuid.uuid4())
        new_review = Review(
            id=review_id,
            user_id=user_id,
            airline_id=review_data.airline_id,
            rating=review_data.rating,
            content=review_data.content,
            images=review_data.images,
            created_at=datetime.utcnow().isoformat(),
            user_nickname="Demo User" # 데모
        )
        self.collection.document(review_id).set(new_review.dict())
        return new_review

    async def get_airline_reviews(self, airline_id: str) -> List[Review]:
        docs = self.collection.where("airline_id", "==", airline_id).stream()
        return [Review(**doc.to_dict()) for doc in docs]

    async def get_my_reviews(self, user_id: str) -> List[Review]:
        docs = self.collection.where("user_id", "==", user_id).stream()
        return [Review(**doc.to_dict()) for doc in docs]
