import threading
import asyncio  # NUEVO: Para tareas asíncronas
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
import logging
import os

from strawberry.fastapi import GraphQLRouter
from strawberry.dataloader import DataLoader  # NUEVO: Para el Dataloader
from app.consumer import start_consuming
from app.db.seed import create_db_and_tables  # TODO: Asegúrate que esta sea async
from app.db.utils import get_session, engine  # NUEVO: Importa el get_session asíncrono
from sqlmodel.ext.asyncio.session import AsyncSession  # NUEVO
from app.graphql.schema import schema

from app.graphql.dataloaders import load_ratings_by_movie_ids

from app.routers import recommendations_router, rankings_router, visits_router
from fastapi.middleware.cors import CORSMiddleware
from app.security import get_current_user

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(threadName)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


# --- 2. ARREGLO DEL LIFESPAN ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    # TODO: Esta función también debe ser 'async' y usar 'await engine.run_sync(SQLModel.metadata.create_all)'
    # De lo contrario, bloqueará el inicio de la app.

    # 🚩 NO USES threading.Thread en una app async. Bloquea el event loop.
    # consumer_thread = threading.Thread(target=start_consuming)
    # consumer_thread.daemon = True
    # consumer_thread.start()

    # ✅ USA asyncio.create_task para tareas en segundo plano
    logging.info("Iniciando consumidor de RabbitMQ en segundo plano...")
    consumer_task = asyncio.create_task(
        start_consuming()
    )  # Asume que start_consuming es 'async def'

    yield

    print("Apagando la aplicación...")
    consumer_task.cancel()  # Cancela la tarea al apagar


# --- 1. ARREGLO DE GRAPHQL (EL MÁS IMPORTANTE) ---


# NUEVO: Esta función define el "contexto" de GraphQL para CADA petición.
async def get_context(
    session: AsyncSession = Depends(get_session),
) -> dict:
    """
    Inyecta la sesión de DB y los Dataloaders en el contexto de GraphQL.
    """
    return {
        "db": session,
        # Creamos una instancia del Dataloader POR PETICIÓN
        "rating_loader": DataLoader(load_fn=load_ratings_by_movie_ids),
    }


# NUEVO: Pasa el 'context_getter' al router
graphql_app = GraphQLRouter(schema, context_getter=get_context)


app = FastAPI(
    lifespan=lifespan, swagger_ui_parameters={"syntaxHighlight": {"theme": "monokai"}}
)

app.include_router(recommendations_router)
app.include_router(rankings_router)
# Esta ruta ahora usará 'get_context' en cada llamada
app.include_router(graphql_app, prefix="/graphql", tags=["graphql"])
app.include_router(visits_router, dependencies=[Depends(get_current_user)])


origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    os.getenv("FE_URL", ""),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "Server working great!"}