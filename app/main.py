from fastapi import FastAPI
from app.database import database
from app.api.v1.endpoints.vehicles import router as vehicles_router


app = FastAPI()
app.include_router(vehicles_router)

@app.on_event("startup")
async def startup():
    await database["vehicles"].create_index("plate", unique=True)

@app.get("/health")
async def health_check():
    await database.command("ping")
    return {"status": "ok"}