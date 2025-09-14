# tests/test_graphql_ordering.py
import re
import unicodedata
from datetime import date
from typing import Generator

import pytest
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy import text

# intentamos importar el módulo que contiene `schema` y `get_session`.
# Ajusta la lista si tu módulo está en un path distinto.
POSSIBLE_MODULES = [
    "app.graphql",           # ejemplo común
    "app.graphql.schema",
    "app.schema",
    "app.graphql_schema",
    "app.api.graphql",
]

schema_module = None
for m in POSSIBLE_MODULES:
    try:
        schema_module = __import__(m, fromlist=["schema", "get_session"])
        if hasattr(schema_module, "schema"):
            break
    except Exception:
        schema_module = None

if schema_module is None:
    raise ImportError(
        "No pude encontrar el módulo que exporta `schema`. "
        "Asegurate de que el esquema Strawberry esté en alguno de: "
        f"{POSSIBLE_MODULES} y que exporte la variable `schema`."
    )

# Importa modelos reales desde app.models (tu código los define)
from app.models import Movie as DBMovie, Genre as DBGenre, Platform as DBPlatform  # type: ignore

# Normalización para comparar títulos (igual que en tests anteriores)
def _normalize_title_for_sort(title: str) -> str:
    if title is None:
        return ""
    s = title.lower().strip()
    s = re.sub(r'^[^\w\d]+', '', s)
    s = re.sub(r'^(el |la |los |las |the |a |an )', '', s)
    nkfd = unicodedata.normalize('NFKD', s)
    s = ''.join([c for c in nkfd if not unicodedata.combining(c)])
    s = re.sub(r'\s+', ' ', s).strip()
    return s

@pytest.fixture
def in_memory_db(tmp_path) -> Generator[Session, None, None]:
    """
    Crea una DB SQLite en memoria, crea las tablas a partir de SQLModel metadata
    y devuelve una Session que se puede usar en tests.
    """
    # Usamos sqlite en memoria con URI que mantiene la misma DB en múltiples conexiones
    database_url = "sqlite:///:memory:"
    engine = create_engine(database_url, echo=False)

    # Crear todas las tablas definidas por SQLModel (usa tus modelos reales)
    SQLModel.metadata.create_all(engine)

    # Poblar con datos de prueba
    with Session(engine) as session:
        # Crear géneros / plataformas si hacen falta (no imprescindibles para sort)
        g1 = DBGenre(nombre="Acción")
        g2 = DBGenre(nombre="Terror")
        session.add_all([g1, g2])
        session.commit()

        # Películas con títulos pensados para probar ordenamiento
        sample_movies = [
            DBMovie(titulo="El Club de la Lucha", sinopsis="", duracionMinutos=139, fechaEstreno=date(1999,10,15)),
            DBMovie(titulo="28 años después", sinopsis="", duracionMinutos=94, fechaEstreno=date(2002,11,1)),
            DBMovie(titulo="Annabelle", sinopsis="", duracionMinutos=99, fechaEstreno=date(2014,10,3)),
            DBMovie(titulo="amateur", sinopsis="", duracionMinutos=100, fechaEstreno=date(2018,5,20)),
            DBMovie(titulo="El abismo secreto", sinopsis="", duracionMinutos=120, fechaEstreno=date(2015,7,7)),
            DBMovie(titulo="Ángel caído", sinopsis="", duracionMinutos=110, fechaEstreno=date(2020,1,1)),
            DBMovie(titulo="Working Man", sinopsis="", duracionMinutos=95, fechaEstreno=date(2019,4,26)),
            DBMovie(titulo="Alien: Romulus", sinopsis="", duracionMinutos=110, fechaEstreno=date(2023,8,1)),
            DBMovie(titulo="The Amazing Spider-Man", sinopsis="", duracionMinutos=136, fechaEstreno=date(2012,6,7)),
            DBMovie(titulo="A Tale of Two Cities", sinopsis="", duracionMinutos=125, fechaEstreno=date(1935,4,12)),
        ]
        session.add_all(sample_movies)
        session.commit()

        # Retornamos la sesión ligada al engine
        yield session

        # No es necesario borrar, la DB en memoria desaparecerá al salir

def _get_session_generator(session: Session):
    """
    Devuelve un generador compatible con next(get_session()) que usa la session provista.
    """
    def gen():
        try:
            yield session
        finally:
            # no cerramos aquí porque el fixture controla el scope
            pass
    return gen

def test_peliculas_sort_titulo_asc_desc(in_memory_db, monkeypatch):
    """
    Comprueba que:
      - sort: "titulo" devuelve una lista cuyo normalized-titles está ordenada ascendentemente.
      - sort: "titulo_desc" devuelve la inversión exacta de la ascendente.
    """
    # monkeypatch al get_session que usa el resolver (en el módulo del schema)
    # el resolver hace: db_session: Session = next(get_session())
    gen = _get_session_generator(in_memory_db)
    monkeypatch.setattr(schema_module, "get_session", gen)

    # Query ascendiente
    query_asc = '''
    query {
      peliculas(sort: "titulo") {
        id
        titulo
      }
    }
    '''
    # Query descendente (según tu schema usa "titulo_desc")
    query_desc = '''
    query {
      peliculas(sort: "titulo_desc") {
        id
        titulo
      }
    }
    '''

    # Ejecutar queries con strawberry directamente desde el schema importado
    result_asc = schema_module.schema.execute_sync(query_asc)
    result_desc = schema_module.schema.execute_sync(query_desc)

    # Verificamos que no hayan ocurrido errores GraphQL
    assert result_asc.errors is None, f"Errores GraphQL: {result_asc.errors}"
    assert result_desc.errors is None, f"Errores GraphQL: {result_desc.errors}"

    movies_asc = result_asc.data["peliculas"]
    movies_desc = result_desc.data["peliculas"]

    assert movies_asc and movies_desc, "Ambas consultas deberían devolver resultados de prueba"

    titles_asc = [m["titulo"] or "" for m in movies_asc]
    titles_desc = [m["titulo"] or "" for m in movies_desc]

    # Normalizar para comparar (evita issues por tildes / mayúsculas)
    norm_asc = [_normalize_title_for_sort(t) for t in titles_asc]
    norm_desc = [_normalize_title_for_sort(t) for t in titles_desc]

    # 1) Normalized asc debería estar ordenado
    assert norm_asc == sorted(norm_asc), (
        "La lista ascendente normalizada no está ordenada. "
        f"Normalized sample: {norm_asc}"
    )

    # 2) Descendente debe ser la inversión exacta de ascendente (comprobación fuerte)
    assert norm_desc == list(reversed(norm_asc)), (
        "La lista descendente normalizada no es la inversión exacta de la ascendente. "
        f"Norm asc sample: {norm_asc}, Norm desc sample: {norm_desc}"
    )
