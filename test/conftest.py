import pytest
import os
from sqlmodel import SQLModel, create_engine
# SQLite in-memory tests need a small compiler fallback for PostgreSQL's JSONB
# Some models use JSONB (Postgres) which the SQLite compiler doesn't know how
# to render. During tests we create an in-memory SQLite DB, so provide a
# tiny monkeypatch that lets the SQLite DDL compiler emit a JSON/TEXT
# column type for JSONB so table creation succeeds.
try:
    from sqlalchemy.dialects.sqlite.base import SQLiteTypeCompiler as _SQLiteTypeCompiler

    def _visit_JSONB(self, type_, **kw):
        # Emit a JSON affinity type for SQLite. SQLite accepts arbitrary
        # type names, and this keeps DDL simple for tests.
        return "JSON"

    _SQLiteTypeCompiler.visit_JSONB = _visit_JSONB
except Exception:
    # If this fails, tests will continue and the original error will show
    # when attempting to create tables. We swallow here to avoid import-time
    # crashes on environments where dialect internals differ.
    pass
from sqlalchemy.pool import StaticPool

# Import modules para sobrescribir sus referencias a engine/get_engine
import app.db.utils as db_utils
import app.db.seed as seed_module


@pytest.fixture(scope="session", autouse=True)
def sqlite_memory_db():
    """Fixture global que sustituye el engine por un SQLite en memoria.

    - Reemplaza `app.db.utils.engine` y `app.db.utils.get_engine` para que
      el resto de la app use SQLite durante los tests.
    - Reemplaza también la referencia `get_engine` dentro de `app.db.seed`
      (seed importa `get_engine` al nivel de módulo) para asegurar que
      el seeding se ejecute sobre el engine en memoria.
    - Ejecuta la creación de tablas y el seeding una vez por sesión.
    """
    sqlite_url = "sqlite:///:memory:"
    engine = create_engine(
        sqlite_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    # Sobrescribir en app.db.utils
    db_utils.engine = engine
    db_utils.get_engine = lambda: engine

    # Sobrescribir la referencia importada dentro de seed_module
    try:
        seed_module.get_engine = lambda: engine
    except Exception:
        pass

    # Crear tablas en el engine en memoria
    SQLModel.metadata.create_all(engine)

    # Intentar ejecutar el seeding (usará la referencia sobrescrita)
    try:
        seed_module.seed_initial_data()
    except Exception as exc:
        # Si el seed falla por cualquier razón, no detener la suite; los
        # tests unitarios pueden parchear/insertar datos específicos.
        print("Warning: seed_initial_data() falló en conftest (continuando):", exc)

    yield

    # Teardown
    try:
        engine.dispose()
    except Exception:
        pass
