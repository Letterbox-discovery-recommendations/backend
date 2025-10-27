from sqlmodel import SQLModel, Field
from datetime import date
from typing import Optional


class User(SQLModel, table=True):
    """Modelo para almacenar información básica de usuarios."""
    id: str = Field(primary_key=True, description="ID único del usuario")
    name: str = Field(description="Nombre completo del usuario")
    country: str = Field(description="Código del país (ej: AR, US, MX)")
    registration_date: date = Field(description="Fecha de registro del usuario")
    profile_picture_url: Optional[str] = Field(default=None, description="URL de la foto de perfil")

    class Config:
        table_name = "users"
