from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user
from app.schemas.paginated_response import (
    PaginatedVehicleResponse,
)
from app.schemas.vehicle import (
    AssignDriverRequest,
    VehicleCreate,
    VehicleResponse,
)
from app.schemas.vehicle_query import (
    VehicleQueryParams,
)
from app.services import vehicle_service
from app.services.vehicle_service import (
    DriverAlreadyAssignedError,
    DriverNotFoundError,
    DuplicatePlateError,
)

router = APIRouter()


@router.post(
    "/vehicles",
    response_model=VehicleResponse,
)
async def create_vehicle(
    vehicle: VehicleCreate,
    current_user: str = Depends(
        get_current_user,
    ),
):
    try:
        return await vehicle_service.create_vehicle(
            vehicle,
        )
    except DuplicatePlateError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error


@router.get(
    "/vehicles",
    response_model=PaginatedVehicleResponse,
)
async def list_vehicles(
    params: VehicleQueryParams = Depends(),
    current_user: str = Depends(
        get_current_user,
    ),
):
    return await vehicle_service.list_vehicles(
        params,
    )


@router.get(
    "/vehicles/{vehicle_id}",
    response_model=VehicleResponse,
)
async def get_vehicle(
    vehicle_id: str,
    current_user: str = Depends(
        get_current_user,
    ),
):
    vehicle = await vehicle_service.get_vehicle(
        vehicle_id,
    )

    if vehicle is None:
        raise HTTPException(
            status_code=404,
            detail="Vehículo no encontrado",
        )

    return vehicle


@router.put(
    "/vehicles/{vehicle_id}",
    response_model=VehicleResponse,
)
async def update_vehicle(
    vehicle_id: str,
    vehicle: VehicleCreate,
    current_user: str = Depends(
        get_current_user,
    ),
):
    updated_vehicle = (
        await vehicle_service.update_vehicle(
            vehicle_id,
            vehicle,
        )
    )

    if updated_vehicle is None:
        raise HTTPException(
            status_code=404,
            detail="Vehículo no encontrado",
        )

    return updated_vehicle


@router.delete(
    "/vehicles/{vehicle_id}",
)
async def delete_vehicle(
    vehicle_id: str,
    current_user: str = Depends(
        get_current_user,
    ),
):
    deleted = await vehicle_service.delete_vehicle(
        vehicle_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Vehículo no encontrado",
        )

    return {
        "message": "Vehículo eliminado",
    }


@router.patch(
    "/vehicles/{vehicle_id}/assign-driver",
    response_model=VehicleResponse,
)
async def assign_driver(
    vehicle_id: str,
    data: AssignDriverRequest,
    current_user: str = Depends(
        get_current_user,
    ),
):
    try:
        updated_vehicle = (
            await vehicle_service.assign_driver(
                vehicle_id,
                data.driver_id,
            )
        )
    except DriverNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
    except DriverAlreadyAssignedError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    if updated_vehicle is None:
        raise HTTPException(
            status_code=404,
            detail="Vehículo no encontrado",
        )

    return updated_vehicle