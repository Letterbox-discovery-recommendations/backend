from pydantic import BaseModel, Field

from app.models.actor import Actor

class Movie(BaseModel):
    id: int = Field(..., description="The unique identifier for the movie")
    title: str = Field(..., description="The title of the movie")
    description: str = Field(..., description="A brief description of the movie")
    release_year: int = Field(..., description="The year the movie was released")
    director: str = Field(..., description="The director of the movie")
    cast: list[Actor] = Field(..., description="The cast of the movie")
