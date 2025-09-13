from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.db.config import create_db_and_tables, seed_initial_data
from app.routers import actores_router
from fastapi.middleware.cors import CORSMiddleware
from app.routers.recommendations import router as recommendations_router
from strawberry.fastapi import GraphQLRouter
from app.graphql.schema import schema

# Crea el router de GraphQL


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    seed_initial_data()
    yield
    print("Apagando la aplicación...")


graphql_app = GraphQLRouter(schema)


app = FastAPI(lifespan=lifespan)

app.include_router(actores_router)
app.include_router(recommendations_router)
app.include_router(graphql_app, prefix="/graphql")


origins = [
    "http://localhost:5173",
    "http://localhost:3000",
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
