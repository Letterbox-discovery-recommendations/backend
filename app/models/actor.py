from pydantic import BaseModel, Field

class Actor(BaseModel):
    id: int = Field(..., description="The unique identifier for the actor")
    name: str = Field(..., description="The name of the actor")
    age: int = Field(..., description="The age of the actor")
    gender: str = Field(..., description="The gender of the actor")
    role: str = Field(..., description="The role of the actor in the film")