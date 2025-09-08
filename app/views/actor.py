from sqlmodel import SQLModel


class ActorNombres(SQLModel):
    id: int
    name: str
