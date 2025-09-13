from typing import List
from fastapi import routing, Depends
from sqlmodel import Session, select
from app.views import ActorNombres
from app.db.config import get_session
from app.models import Actor


router = routing.APIRouter(
    prefix="/api/v1/actores",
    tags=["Actores"],
)


@router.get("/nombres", response_model=List[ActorNombres])
def obtener_nombres_actores(db_session: Session = Depends(get_session)):
    statement = select(Actor)
    actors = db_session.exec(statement).all()

    return actors
