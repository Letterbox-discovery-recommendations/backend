from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.db.config import create_db_and_tables, seed_initial_data
from app.routers import actores_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    seed_initial_data()
    yield
    print("Apagando la aplicación...")


app = FastAPI(lifespan=lifespan)

app.include_router(actores_router)


@app.get("/")
def health_check():
    return {"status": "Server working great!"}
