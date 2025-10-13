from sqlmodel import Field, SQLModel
from datetime import datetime


class Follow(SQLModel, table=True):
    """
    Representa la relación de seguimiento entre usuarios.
    Un usuario (follower) sigue a otro usuario (followed).
    """
    id: int | None = Field(default=None, primary_key=True)
    follower_id: int = Field(nullable=False, index=True)
    followed_id: int = Field(nullable=False, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
