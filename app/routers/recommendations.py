from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.db.utils import get_session
from app.models import RecommendationResponse, GroupRecommendationRequest
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


@router.post("/group", response_model=List[RecommendationResponse])
async def get_group_recommendations(
    request: GroupRecommendationRequest,
    db_session: Session = Depends(get_session),
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Obtiene recomendaciones grupales combinando las preferencias de múltiples usuarios.
    
    - **user_ids**: Lista de 2 a 10 IDs de usuarios del grupo
    - Requiere que el usuario autenticado esté incluido en el grupo
    - Combina perfiles individuales usando content-based y collaborative filtering
    - Pondera por actividad de cada usuario (número de reseñas)
    - Retorna películas que reflejan los intereses comunes del grupo
    """
    # Validar que el usuario actual esté en el grupo
    if current_user.user_id not in request.user_ids:
        raise HTTPException(
            status_code=403,
            detail="El usuario autenticado debe ser parte del grupo para obtener recomendaciones grupales"
        )
    
    engine = Recommendations(db_session)
    
    try:
        recommendations = engine.get_group_recommendations(request.user_ids)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    response = [
        RecommendationResponse(movie=item["movie"], score=item["score"])
        for item in recommendations
    ]
    return response
