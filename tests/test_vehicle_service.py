from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bson import ObjectId
from pydantic import ValidationError
from pymongo.errors import DuplicateKeyError

from app.schemas.vehicle import VehicleCreate
from app.services import vehicle_service
from app.services.vehicle_service import DuplicatePlateError


class TestVehicleService:
    @pytest.mark.asyncio
    async def test_create_vehicle_success(self):
        vehicle_id = ObjectId()

        vehicle_data = VehicleCreate(
            plate="pda-1234",
            brand="Toyota",
            model="Hilux",
            year=2020,
            capacity_kg=1000,
            status="active",
        )

        created_vehicle = {
            "_id": vehicle_id,
            "plate": "PDA-1234",
            "brand": "Toyota",
            "model": "Hilux",
            "year": 2020,
            "capacity_kg": 1000,
            "status": "active",
        }

        mock_collection = MagicMock()
        mock_collection.insert_one = AsyncMock(
            return_value=MagicMock(
                inserted_id=vehicle_id,
            ),
        )
        mock_collection.find_one = AsyncMock(
            return_value=created_vehicle,
        )

        mock_database = {
            "vehicles": mock_collection,
        }

        with patch.object(
            vehicle_service,
            "database",
            mock_database,
        ):
            result = await vehicle_service.create_vehicle(
                vehicle_data,
            )

        assert result == {
            "id": str(vehicle_id),
            "plate": "PDA-1234",
            "brand": "Toyota",
            "model": "Hilux",
            "year": 2020,
            "capacity_kg": 1000,
            "status": "active",
            "driver": None,
        }

        mock_collection.insert_one.assert_awaited_once_with(
            vehicle_data.model_dump(),
        )

    @pytest.mark.asyncio
    async def test_create_vehicle_raises_error_when_plate_is_duplicate(
        self,
    ):
        vehicle_data = VehicleCreate(
            plate="PDA-1234",
            brand="Toyota",
            model="Hilux",
            year=2020,
            capacity_kg=1000,
            status="active",
        )

        mock_collection = MagicMock()
        mock_collection.insert_one = AsyncMock(
            side_effect=DuplicateKeyError(
                "duplicate",
            ),
        )

        mock_database = {
            "vehicles": mock_collection,
        }

        with patch.object(
            vehicle_service,
            "database",
            mock_database,
        ):
            with pytest.raises(
                DuplicatePlateError,
            ) as error:
                await vehicle_service.create_vehicle(
                    vehicle_data,
                )

        assert (
            str(error.value)
            == "La placa ya está registrada"
        )

    @pytest.mark.asyncio
    async def test_list_vehicles_success(self):
        vehicle_id_1 = ObjectId()
        vehicle_id_2 = ObjectId()
        driver_id = ObjectId()

        stored_vehicles = [
            {
                "_id": vehicle_id_1,
                "plate": "PDA-1234",
                "brand": "Toyota",
                "model": "Hilux",
                "year": 2020,
                "capacity_kg": 1000,
                "status": "active",
                "driver_id": driver_id,
            },
            {
                "_id": vehicle_id_2,
                "plate": "ABC-5678",
                "brand": "Chevrolet",
                "model": "D-Max",
                "year": 2022,
                "capacity_kg": 1200,
                "status": "inactive",
            },
        ]

        stored_drivers = [
            {
                "_id": driver_id,
                "name": "José López",
                "license": "ARTE-879",
            },
        ]

        vehicle_cursor = MagicMock()
        vehicle_cursor.__aiter__.return_value = stored_vehicles

        driver_cursor = MagicMock()
        driver_cursor.__aiter__.return_value = stored_drivers

        vehicle_collection = MagicMock()
        vehicle_collection.find.return_value = vehicle_cursor

        driver_collection = MagicMock()
        driver_collection.find.return_value = driver_cursor

        mock_database = {
            "vehicles": vehicle_collection,
            "drivers": driver_collection,
        }

        with patch.object(
            vehicle_service,
            "database",
            mock_database,
        ):
            result = await vehicle_service.list_vehicles()

        assert result == [
            {
                "id": str(vehicle_id_1),
                "plate": "PDA-1234",
                "brand": "Toyota",
                "model": "Hilux",
                "year": 2020,
                "capacity_kg": 1000,
                "status": "active",
                "driver": {
                    "id": str(driver_id),
                    "name": "José López",
                    "license": "ARTE-879",
                },
            },
            {
                "id": str(vehicle_id_2),
                "plate": "ABC-5678",
                "brand": "Chevrolet",
                "model": "D-Max",
                "year": 2022,
                "capacity_kg": 1200,
                "status": "inactive",
                "driver": None,
            },
        ]

        driver_collection.find.assert_called_once_with(
            {
                "_id": {
                    "$in": [driver_id],
                },
            },
        )

    @pytest.mark.asyncio
    async def test_get_vehicle_returns_none_when_id_is_invalid(
        self,
    ):
        result = await vehicle_service.get_vehicle(
            "no-es-un-object-id",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_get_vehicle_returns_none_when_vehicle_does_not_exist(
        self,
    ):
        vehicle_id = ObjectId()

        mock_collection = MagicMock()
        mock_collection.find_one = AsyncMock(
            return_value=None,
        )

        mock_database = {
            "vehicles": mock_collection,
        }

        with patch.object(
            vehicle_service,
            "database",
            mock_database,
        ):
            result = await vehicle_service.get_vehicle(
                str(vehicle_id),
            )

        assert result is None


class TestVehicleValidations:
    def test_vehicle_create_raises_validation_error_when_plate_format_is_invalid(
        self,
    ):
        with pytest.raises(ValidationError):
            VehicleCreate(
                plate="PDA1234",
                brand="Toyota",
                model="Hilux",
                year=2020,
                capacity_kg=1000,
                status="active",
            )

    def test_vehicle_create_raises_validation_error_when_year_is_invalid(
        self,
    ):
        with pytest.raises(ValidationError):
            VehicleCreate(
                plate="PDA-1234",
                brand="Toyota",
                model="Hilux",
                year=1989,
                capacity_kg=1000,
                status="active",
            )

    def test_vehicle_create_raises_validation_error_when_capacity_is_zero(
        self,
    ):
        with pytest.raises(ValidationError):
            VehicleCreate(
                plate="PDA-1234",
                brand="Toyota",
                model="Hilux",
                year=2020,
                capacity_kg=0,
                status="active",
            )