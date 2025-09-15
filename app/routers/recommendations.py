from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db.config import get_session
from app.models import RecommendationResponse
from app.services import Recommendations

router = APIRouter(prefix="/api/v1/recommendations", tags=["recommendations"])


@router.get("/content/{user_id}", response_model=List[RecommendationResponse])
async def get_content_recommendations(user_id: int,db_session: Session = Depends(get_session)):
    engine = Recommendations(db_session)
    recommendations = engine.get_recommendations(user_id)
    response = [
        RecommendationResponse(movie=movie, score=score)
        for movie, score in recommendations
    ]
    return response


@router.get("/collaborative/{user_id}", response_model=List[RecommendationResponse])
async def get_collaborative_recommendations(user_id: int, db_session: Session = Depends(get_session)):
    engine = Recommendations(db_session)
    recommendations = engine.get_collaborative_recommendations(user_id)

    response = [
        RecommendationResponse(movie=item["movie"], score=item["score"])
        for item in recommendations
    ]
    return response
