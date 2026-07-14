from unittest.mock import AsyncMock, MagicMock, patch
from pydantic import ValidationError

import pytest
from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from app.schemas.driver import DriverCreate
from app.services import driver_service, vehicle_service
from app.services.driver_service import DuplicateLicenseError
from app.services.vehicle_service import (
    DriverAlreadyAssignedError,
    DriverNotFoundError,
)


class TestDriverService:
    @pytest.mark.asyncio
    async def test_create_driver_success(self):
        driver_id = ObjectId()

        driver_data = DriverCreate(
            name="José López",
            license="1712345678",
        )

        stored_driver = {
            "_id": driver_id,
            "name": "José López",
            "license": "1712345678",
        }

        mock_collection = MagicMock()
        mock_collection.insert_one = AsyncMock(
            return_value=MagicMock(
                inserted_id=driver_id,
            ),
        )
        mock_collection.find_one = AsyncMock(
            return_value=stored_driver,
        )

        mock_database = {
            "drivers": mock_collection,
        }

        with patch.object(
            driver_service,
            "database",
            mock_database,
        ):
            result = await driver_service.create_driver(
                driver_data,
            )

        assert result == {
            "id": str(driver_id),
            "name": "José López",
            "license": "1712345678",
        }

        mock_collection.insert_one.assert_awaited_once_with(
            driver_data.model_dump(),
        )

    @pytest.mark.asyncio
    async def test_create_driver_raises_error_when_license_is_duplicate(
        self,
    ):
        driver_data = DriverCreate(
            name="José López",
            license="1712345678",
        )

        mock_collection = MagicMock()
        mock_collection.insert_one = AsyncMock(
            side_effect=DuplicateKeyError(
                "duplicate",
            ),
        )

        mock_database = {
            "drivers": mock_collection,
        }

        with patch.object(
            driver_service,
            "database",
            mock_database,
        ):
            with pytest.raises(
                DuplicateLicenseError,
            ) as error:
                await driver_service.create_driver(
                    driver_data,
                )

        assert (
            str(error.value)
            == "La licencia ya está registrada"
        )


class TestAssignDriver:
    @pytest.mark.asyncio
    async def test_assign_driver_success(self):
        vehicle_id = ObjectId()
        driver_id = ObjectId()

        stored_vehicle = {
            "_id": vehicle_id,
            "plate": "ABC-1234",
            "brand": "Toyota",
            "model": "Hilux",
            "year": 2022,
            "capacity_kg": 1500,
            "status": "active",
        }

        stored_driver = {
            "_id": driver_id,
            "name": "José López",
            "license": "1712345678",
        }

        updated_vehicle = {
            **stored_vehicle,
            "driver_id": driver_id,
        }

        vehicle_collection = MagicMock()
        vehicle_collection.find_one = AsyncMock(
            side_effect=[
                stored_vehicle,
                None,
                updated_vehicle,
            ],
        )
        vehicle_collection.update_one = AsyncMock()

        driver_collection = MagicMock()
        driver_collection.find_one = AsyncMock(
            side_effect=[
                stored_driver,
                stored_driver,
            ],
        )

        mock_database = {
            "vehicles": vehicle_collection,
            "drivers": driver_collection,
        }

        with patch.object(
            vehicle_service,
            "database",
            mock_database,
        ):
            result = await vehicle_service.assign_driver(
                str(vehicle_id),
                str(driver_id),
            )

        assert result == {
            "id": str(vehicle_id),
            "plate": "ABC-1234",
            "brand": "Toyota",
            "model": "Hilux",
            "year": 2022,
            "capacity_kg": 1500,
            "status": "active",
            "driver": {
                "id": str(driver_id),
                "name": "José López",
                "license": "1712345678",
            },
        }

        vehicle_collection.update_one.assert_awaited_once_with(
            {"_id": vehicle_id},
            {
                "$set": {
                    "driver_id": driver_id,
                },
            },
        )

    @pytest.mark.asyncio
    async def test_assign_driver_raises_error_when_driver_does_not_exist(
        self,
    ):
        vehicle_id = ObjectId()
        driver_id = ObjectId()

        vehicle_collection = MagicMock()
        vehicle_collection.find_one = AsyncMock(
            return_value={
                "_id": vehicle_id,
            },
        )

        driver_collection = MagicMock()
        driver_collection.find_one = AsyncMock(
            return_value=None,
        )

        mock_database = {
            "vehicles": vehicle_collection,
            "drivers": driver_collection,
        }

        with patch.object(
            vehicle_service,
            "database",
            mock_database,
        ):
            with pytest.raises(
                DriverNotFoundError,
            ) as error:
                await vehicle_service.assign_driver(
                    str(vehicle_id),
                    str(driver_id),
                )

        assert (
            str(error.value)
            == "Conductor no encontrado"
        )

    @pytest.mark.asyncio
    async def test_assign_driver_raises_error_when_driver_is_already_assigned(
        self,
    ):
        vehicle_id = ObjectId()
        other_vehicle_id = ObjectId()
        driver_id = ObjectId()

        vehicle_collection = MagicMock()
        
        vehicle_collection.find_one = AsyncMock(
            side_effect=[
                {
                    "_id": vehicle_id,
                },
                {
                    "_id": other_vehicle_id,
                    "driver_id": driver_id,
                },
            ],
        )

        vehicle_collection.update_one = AsyncMock()
        
        driver_collection = MagicMock()
        driver_collection.find_one = AsyncMock(
            return_value={
                "_id": driver_id,
                "name": "José López",
                "license": "1712345678",
            },
        )

        mock_database = {
            "vehicles": vehicle_collection,
            "drivers": driver_collection,
        }

        with patch.object(
            vehicle_service,
            "database",
            mock_database,
        ):
            with pytest.raises(
                DriverAlreadyAssignedError,
            ) as error:
                await vehicle_service.assign_driver(
                    str(vehicle_id),
                    str(driver_id),
                )

        assert (
            str(error.value)
            == "El conductor ya está asignado a otro vehículo"
        )

        vehicle_collection.update_one.assert_not_awaited()


class TestDriverValidations:
    def test_driver_rejects_license_with_letters(
        self,
    ):
        with pytest.raises(ValidationError):
            DriverCreate(
                name="José López",
                license="ABC1234567",
            )

    def test_driver_rejects_license_with_less_than_ten_digits(
        self,
    ):
        with pytest.raises(ValidationError):
            DriverCreate(
                name="José López",
                license="123456789",
            )

    def test_driver_rejects_license_with_more_than_ten_digits(
        self,
    ):
        with pytest.raises(ValidationError):
            DriverCreate(
                name="José López",
                license="12345678901",
            )