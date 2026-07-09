from fastapi import FastAPI
from app.database import database
from app.api.v1.endpoints.vehicles import router as vehicles_router
from app.api.v1.endpoints.auth import router as auth_router

app = FastAPI()
app.include_router(vehicles_router)
app.include_router(auth_router)

@app.get("/health")
async def health_check():
    await database.command("ping")
    return {"status": "ok"}
