from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db.utils import get_session
from app.models import RecommendationResponse
from app.security import get_current_user, TokenPayload
from app.services import Recommendations

router = APIRouter(prefix="/api/v1/recommendations", tags=["recommendations"])


@router.get("/content", response_model=List[RecommendationResponse])
async def get_content_recommendations(db_session: Session = Depends(get_session),current_user: TokenPayload = Depends(get_current_user)):
    engine = Recommendations(db_session)
    recommendations = engine.get_recommendations(current_user.user_id)
    response = [
        RecommendationResponse(movie=movie, score=score)
        for movie, score in recommendations
    ]
    return response


@router.get("/collaborative", response_model=List[RecommendationResponse])
async def get_collaborative_recommendations(db_session: Session = Depends(get_session),current_user: TokenPayload = Depends(get_current_user)):
    engine = Recommendations(db_session)
    recommendations = engine.get_collaborative_recommendations(current_user.user_id)

    response = [
        RecommendationResponse(movie=item["movie"], score=item["score"])
        for item in recommendations
    ]
    return response
