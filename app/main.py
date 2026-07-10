from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.vehicles import router as vehicles_router
from app.database import database


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database["vehicles"].create_index("plate", unique=True)
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(vehicles_router)
app.include_router(auth_router)


@app.get("/health")
async def health_check():
    await database.command("ping")
    return {"status": "ok"}