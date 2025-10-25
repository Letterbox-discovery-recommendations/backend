from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db.utils import get_session
from app.models import RecommendationResponse, GroupRecommendationRequest, Follow
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


@router.get("/friends", response_model=List[int])
async def get_friends(
    db_session: Session = Depends(get_session),
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Obtiene la lista de amigos (seguidores mutuos) del usuario autenticado.
    
    Un amigo es alguien que sigue al usuario Y el usuario lo sigue a él.
    
    Returns:
        Lista de IDs de amigos
    """
    engine = Recommendations(db_session)
    friends = engine.get_followed(current_user.user_id)
    
    return friends


@router.post("/group", response_model=List[RecommendationResponse])
async def get_group_recommendations(
    request: GroupRecommendationRequest,
    db_session: Session = Depends(get_session),
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Obtiene recomendaciones grupales combinando las preferencias de múltiples usuarios.
    
    Se puede usar de tres formas:
    1. Proporcionar 'user_ids': Lista explícita de IDs de usuarios (2-10 usuarios)
    2. Proporcionar 'base_user_ids': Lista de IDs de usuarios base para crear grupo automáticamente con sus seguidores
    3. Proporcionar 'user_id' y 'friend_ids': Usuario solicitante + lista de amigos seleccionados
    
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
        
        elif request.base_user_ids is not None:
            # Método por seguidores: grupo automático
            recommendations = engine.get_group_recommendations_by_followers(request.base_user_ids)
            
            # Validar que el usuario actual sea uno de los base_users o esté entre sus seguidores
            if current_user.user_id not in request.base_user_ids:
                # Verificar si el usuario actual es seguidor de al menos uno de los base_users
                is_follower_of_any = False
                for base_user_id in request.base_user_ids:
                    follower_check = db_session.exec(
                        select(Follow).where(
                            Follow.follower_id == current_user.user_id,
                            Follow.followed_id == base_user_id
                        )
                    ).first()
                    if follower_check:
                        is_follower_of_any = True
                        break
                
                if not is_follower_of_any:
                    raise HTTPException(
                        status_code=403,
                        detail="Solo los usuarios base o sus seguidores pueden solicitar recomendaciones grupales por seguidores"
                    )
        
        elif request.user_id is not None and request.friend_ids is not None:
            # Nuevo método: usuario + amigos seleccionados
            if request.user_id != current_user.user_id:
                raise HTTPException(
                    status_code=403,
                    detail="El user_id debe ser el del usuario autenticado"
                )
            
            # Verificar que los friend_ids sean realmente amigos del usuario
            user_friends = engine.get_followed(current_user.user_id)
            friend_ids_from_db = user_friends  # get_followed retorna List[int]
            
            invalid_friends = set(request.friend_ids) - set(friend_ids_from_db)
            if invalid_friends:
                raise HTTPException(
                    status_code=400,
                    detail=f"Los siguientes IDs no son amigos del usuario: {list(invalid_friends)}"
                )
            
            # Crear la lista completa de usuarios para el grupo
            group_user_ids = [request.user_id] + request.friend_ids
            recommendations = engine.get_group_recommendations(group_user_ids)
        
        else:
            raise HTTPException(status_code=400, detail="Método de request no válido")
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    response = [
        RecommendationResponse(movie=item["movie"], score=item["score"])
        for item in recommendations
    ]
    return response
