from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.database import database
from app.schemas.vehicle import VehicleCreate


class DuplicatePlateError(Exception):
    pass


def vehicle_helper(vehicle) -> dict:
    return {
        "id": str(vehicle["_id"]),
        "plate": vehicle["plate"],
        "brand": vehicle["brand"],
        "model": vehicle["model"],
        "year": vehicle["year"],
        "capacity_kg": vehicle["capacity_kg"],
        "status": vehicle["status"],
    }


async def create_vehicle(data: VehicleCreate) -> dict:
    existing = await database["vehicles"].find_one({"plate": data.plate})
    if existing:
        raise DuplicatePlateError("La placa ya está registrada")

    result = await database["vehicles"].insert_one(data.model_dump())
    new_vehicle = await database["vehicles"].find_one({"_id": result.inserted_id})
    return vehicle_helper(new_vehicle)


async def list_vehicles() -> list[dict]:
    vehicles = []
    async for vehicle in database["vehicles"].find():
        vehicles.append(vehicle_helper(vehicle))
    return vehicles


async def get_vehicle(vehicle_id: str) -> dict | None:
    try:
        object_id = ObjectId(vehicle_id)
    except Exception:
        return None
    vehicle = await database["vehicles"].find_one({"_id": object_id})
    if vehicle:
        return vehicle_helper(vehicle)
    return None


async def update_vehicle(vehicle_id: str, data: VehicleCreate) -> dict | None:
    try:
        object_id = ObjectId(vehicle_id)
    except Exception:
        return None
    await database["vehicles"].update_one(
        {"_id": object_id},
        {"$set": data.model_dump()},
    )
    updated_vehicle = await database["vehicles"].find_one({"_id": object_id})
    if updated_vehicle:
        return vehicle_helper(updated_vehicle)
    return None


async def delete_vehicle(vehicle_id: str) -> bool:
    try:
        object_id = ObjectId(vehicle_id)
    except Exception:
        return False
    result = await database["vehicles"].delete_one({"_id": object_id})
    return result.deleted_count > 0