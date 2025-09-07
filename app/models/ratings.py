from sqlmodel import Field, SQLModel


class Review(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    movie_id: int = Field(foreign_key="movie.id", nullable=False)
    user_id: int = Field(nullable=False)
    rating: float = Field(nullable=False)
    comment: str | None = None