from sqlmodel import Field, SQLModel
from datetime import datetime


class CachedUser(SQLModel, table=True):
    """
    Caché local de usuarios recibido vía RabbitMQ.
    Almacena información básica de usuarios para consultas locales.
    """
    id: int = Field(primary_key=True)
    name: str = Field(unique=True, index=True)
    profile_picture_url: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)