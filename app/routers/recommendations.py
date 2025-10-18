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
    
    Se puede usar de dos formas:
    1. Proporcionar 'user_ids': Lista explícita de IDs de usuarios (2-10 usuarios)
    2. Proporcionar 'base_user_id': Crea grupo automáticamente con el usuario + sus seguidores
    
    - Requiere que el usuario autenticado esté incluido en el grupo
    - Combina perfiles individuales usando content-based y collaborative filtering
    - Pondera por actividad de cada usuario (número de reseñas)
    - Retorna películas que reflejan los intereses comunes del grupo
    """
    engine = Recommendations(db_session)
    
    try:
        if request.user_ids is not None:
            # Método tradicional: lista explícita de usuarios
            recommendations = engine.get_group_recommendations(request.user_ids)
            
            # Validar que el usuario actual esté en el grupo
            if current_user.user_id not in request.user_ids:
                raise HTTPException(
                    status_code=403,
                    detail="El usuario autenticado debe ser parte del grupo para obtener recomendaciones grupales"
                )
        
        elif request.base_user_id is not None:
            # Método por seguidores: grupo automático
            recommendations = engine.get_group_recommendations_by_followers(request.base_user_id)
            
            # Validar que el usuario actual sea el base_user o esté entre sus seguidores
            # (Esta validación se hace implícitamente en el método, pero podemos agregar más checks si es necesario)
            if current_user.user_id != request.base_user_id:
                # Verificar si el usuario actual es seguidor del base_user
                from app.models import Follow
                is_follower = db_session.exec(
                    select(Follow).where(
                        Follow.follower_id == current_user.user_id,
                        Follow.followed_id == request.base_user_id
                    )
                ).first()
                
                if not is_follower:
                    raise HTTPException(
                        status_code=403,
                        detail="Solo el usuario base o sus seguidores pueden solicitar recomendaciones grupales por seguidores"
                    )
        
        else:
            raise HTTPException(status_code=400, detail="Debe proporcionar 'user_ids' o 'base_user_id'")
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    response = [
        RecommendationResponse(movie=item["movie"], score=item["score"])
        for item in recommendations
    ]
    return response
