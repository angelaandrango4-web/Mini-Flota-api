from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from app.database import database
from app.schemas.vehicle import VehicleCreate
from app.services.driver_service import driver_helper


class DuplicatePlateError(Exception):
    pass


class DriverNotFoundError(Exception):
    pass


class DriverAlreadyAssignedError(Exception):
    pass


def format_vehicle(
    vehicle: dict,
    driver: dict | None,
) -> dict:
    return {
        "id": str(vehicle["_id"]),
        "plate": vehicle.get("plate"),
        "brand": vehicle.get("brand"),
        "model": vehicle.get("model"),
        "year": vehicle.get("year"),
        "capacity_kg": vehicle.get("capacity_kg"),
        "status": vehicle.get("status"),
        "driver": driver,
    }


async def get_driver_data(
    driver_id: ObjectId | None,
) -> dict | None:
    if driver_id is None:
        return None

    driver = await database["drivers"].find_one(
        {"_id": driver_id},
    )

    if driver is None:
        return None

    return driver_helper(driver)


async def vehicle_helper(
    vehicle: dict,
) -> dict:
    driver = await get_driver_data(
        vehicle.get("driver_id"),
    )

    return format_vehicle(
        vehicle,
        driver,
    )


async def create_vehicle(
    data: VehicleCreate,
) -> dict:
    try:
        result = await database["vehicles"].insert_one(
            data.model_dump(),
        )
    except DuplicateKeyError:
        raise DuplicatePlateError(
            "La placa ya está registrada",
        )

    new_vehicle = await database["vehicles"].find_one(
        {"_id": result.inserted_id},
    )

    if new_vehicle is None:
        raise RuntimeError(
            "No se pudo recuperar el vehículo creado",
        )

    return await vehicle_helper(new_vehicle)


async def list_vehicles() -> list[dict]:
    vehicles = []

    async for vehicle in database["vehicles"].find():
        vehicles.append(vehicle)

    driver_ids = {
        vehicle["driver_id"]
        for vehicle in vehicles
        if vehicle.get("driver_id") is not None
    }

    drivers_by_id: dict[ObjectId, dict] = {}

    if driver_ids:
        driver_cursor = database["drivers"].find(
            {
                "_id": {
                    "$in": list(driver_ids),
                },
            },
        )

        async for driver in driver_cursor:
            drivers_by_id[driver["_id"]] = (
                driver_helper(driver)
            )

    return [
        format_vehicle(
            vehicle,
            drivers_by_id.get(
                vehicle.get("driver_id"),
            ),
        )
        for vehicle in vehicles
    ]


async def get_vehicle(
    vehicle_id: str,
) -> dict | None:
    try:
        object_id = ObjectId(vehicle_id)
    except Exception:
        return None

    vehicle = await database["vehicles"].find_one(
        {"_id": object_id},
    )

    if vehicle:
        return await vehicle_helper(vehicle)

    return None


async def update_vehicle(
    vehicle_id: str,
    data: VehicleCreate,
) -> dict | None:
    try:
        object_id = ObjectId(vehicle_id)
    except Exception:
        return None

    await database["vehicles"].update_one(
        {"_id": object_id},
        {
            "$set": data.model_dump(),
        },
    )

    updated_vehicle = await database["vehicles"].find_one(
        {"_id": object_id},
    )

    if updated_vehicle:
        return await vehicle_helper(updated_vehicle)

    return None


async def delete_vehicle(
    vehicle_id: str,
) -> bool:
    try:
        object_id = ObjectId(vehicle_id)
    except Exception:
        return False

    result = await database["vehicles"].delete_one(
        {"_id": object_id},
    )

    return result.deleted_count > 0


async def assign_driver(
    vehicle_id: str,
    driver_id: str,
) -> dict | None:
    try:
        vehicle_object_id = ObjectId(vehicle_id)
        driver_object_id = ObjectId(driver_id)
    except Exception:
        return None

    vehicle = await database["vehicles"].find_one(
        {"_id": vehicle_object_id},
    )

    if vehicle is None:
        return None

    driver = await database["drivers"].find_one(
        {"_id": driver_object_id},
    )

    if driver is None:
        raise DriverNotFoundError(
            "Conductor no encontrado",
        )

    existing_assignment = await database["vehicles"].find_one(
        {
            "driver_id": driver_object_id,
            "_id": {
                "$ne": vehicle_object_id,
            },
        },
    )

    if existing_assignment is not None:
        raise DriverAlreadyAssignedError(
            "El conductor ya está asignado a otro vehículo",
        )

    await database["vehicles"].update_one(
        {"_id": vehicle_object_id},
        {
            "$set": {
                "driver_id": driver_object_id,
            },
        },
    )

    updated_vehicle = await database["vehicles"].find_one(
        {"_id": vehicle_object_id},
    )

    if updated_vehicle is None:
        return None

    return await vehicle_helper(updated_vehicle)