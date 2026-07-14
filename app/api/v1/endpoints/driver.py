from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user
from app.schemas.driver import DriverCreate, DriverResponse
from app.services import driver_service
from app.services.driver_service import DuplicateLicenseError

router = APIRouter()


@router.post(
    "/drivers",
    response_model=DriverResponse,
)
async def create_driver(
    driver: DriverCreate,
    current_user: str = Depends(get_current_user),
):
    try:
        return await driver_service.create_driver(driver)
    except DuplicateLicenseError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@router.get(
    "/drivers",
    response_model=list[DriverResponse],
)
async def list_drivers(
    current_user: str = Depends(get_current_user),
):
    return await driver_service.list_drivers()