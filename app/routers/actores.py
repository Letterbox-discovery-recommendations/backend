from fastapi import routing, Depends
from sqlmodel import Session, select
from app.db.config import get_session
from app.models import RealPerson

router = routing.APIRouter(
    prefix="/api/v1/actores",
    tags=["Actores"],
)


@router.get("/nombres")
def obtener_nombres_actores(db_session: Session = Depends(get_session)):
    statement = select(RealPerson)
    actors = db_session.exec(statement).all()
    return actors
