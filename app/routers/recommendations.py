from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db.config import get_session
from app.models import RecommendationResponse
from app.services import Recommendations

router = APIRouter(prefix="/api/v1/recommendations", tags=["recommendations"])

@router.get("/", response_model=List[RecommendationResponse])
async def health_check(db_session: Session = Depends(get_session)):
    engine = Recommendations(db_session)
    recommendations = engine.get_recommendations()

    response = [
        RecommendationResponse(movie=movie, score=score)
        for movie, score in recommendations
    ]
    return response