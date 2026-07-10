import asyncio

from app.database import database
from app.services.auth_service import hash_password


async def seed():
    existing = await database["users"].find_one({"email": "admin@miniflota.com"})
    if existing:
        print("El usuario semilla ya existe.")
        return

    await database["users"].insert_one({
        "email": "admin@miniflota.com",
        "hashed_password": hash_password("admin123"),
    })
    print("Usuario semilla creado.")


if __name__ == "__main__":
    asyncio.run(seed())