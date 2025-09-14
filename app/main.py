from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.db.config import create_db_and_tables, seed_initial_data
from fastapi.middleware.cors import CORSMiddleware
from app.routers import recommendations_router, rankings_router
from strawberry.fastapi import GraphQLRouter
from app.graphql.schema import schema
import os

# Crea el router de GraphQL


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    seed_initial_data()
    yield
    print("Apagando la aplicación...")


graphql_app = GraphQLRouter(schema)


app = FastAPI(lifespan=lifespan, swagger_ui_parameters={"syntaxHighlight": {"theme": "monokai"}})

app.include_router(recommendations_router)
app.include_router(rankings_router)
app.include_router(graphql_app, prefix="/graphql", tags=["graphql"])


origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    os.getenv("FE_URL",""),
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
