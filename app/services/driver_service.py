from pymongo.errors import DuplicateKeyError

from app.database import database
from app.schemas.driver import DriverCreate


class DuplicateLicenseError(Exception):
    pass


def driver_helper(driver) -> dict:
    return {
        "id": str(driver["_id"]),
        "name": driver.get("name"),
        "license": driver.get("license"),
    }


async def create_driver(data: DriverCreate) -> dict:
    try:
        result = await database["drivers"].insert_one(
            data.model_dump(),
        )
    except DuplicateKeyError:
        raise DuplicateLicenseError(
            "La licencia ya está registrada",
        )

    new_driver = await database["drivers"].find_one(
        {"_id": result.inserted_id},
    )

    return driver_helper(new_driver)


async def list_drivers() -> list[dict]:
    drivers = []

    async for driver in database["drivers"].find():
        drivers.append(driver_helper(driver))

    return drivers