from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings

app = FastAPI()

client = AsyncIOMotorClient(settings.mongodb_url)
database = client["mini_flota"]


@app.get("/health")
async def health_check():
    await database.command("ping")
    return {"status": "ok"}