import math
import re

from bson import ObjectId
from pymongo import ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError

from app.database import database
from app.schemas.vehicle import VehicleCreate
from app.schemas.vehicle_query import (
    VehicleQueryParams,
)
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


async def list_vehicles(
    params: VehicleQueryParams,
) -> dict:
    filters: dict = {}

    if params.status is not None:
        filters["status"] = params.status

    if params.search is not None:
        safe_search = re.escape(params.search)

        filters["$or"] = [
            {
                "plate": {
                    "$regex": safe_search,
                    "$options": "i",
                },
            },
            {
                "brand": {
                    "$regex": safe_search,
                    "$options": "i",
                },
            },
            {
                "model": {
                    "$regex": safe_search,
                    "$options": "i",
                },
            },
        ]

    total = await database["vehicles"].count_documents(
        filters,
    )

    skip = (
        params.page - 1
    ) * params.page_size

    sort_direction = (
        ASCENDING
        if params.order == "asc"
        else DESCENDING
    )

    vehicle_cursor = (
        database["vehicles"]
        .find(filters)
        .sort(
            params.sort_by,
            sort_direction,
        )
        .skip(skip)
        .limit(params.page_size)
    )

    vehicles = []

    async for vehicle in vehicle_cursor:
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

    items = [
        format_vehicle(
            vehicle,
            drivers_by_id.get(
                vehicle.get("driver_id"),
            ),
        )
        for vehicle in vehicles
    ]

    total_pages = (
        math.ceil(total / params.page_size)
        if total > 0
        else 0
    )

    return {
        "items": items,
        "total": total,
        "page": params.page,
        "page_size": params.page_size,
        "total_pages": total_pages,
    }


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
        return await vehicle_helper(
            updated_vehicle,
        )

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

    existing_assignment = await database[
        "vehicles"
    ].find_one(
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

    updated_vehicle = await database[
        "vehicles"
    ].find_one(
        {"_id": vehicle_object_id},
    )

    if updated_vehicle is None:
        return None

    return await vehicle_helper(updated_vehicle)