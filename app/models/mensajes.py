from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import SQLModel, Field, Column  # <-- Importa Column
from typing import Any


class Mensaje(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    evento: str = Field(index=True)
    tipo: str = Field(index=True)

    data: Any | None = Field(
        default=None,
        sa_column=Column(JSONB),
    )