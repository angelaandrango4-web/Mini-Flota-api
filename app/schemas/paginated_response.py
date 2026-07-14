from pydantic import BaseModel

from app.schemas.vehicle import VehicleResponse


class PaginatedVehicleResponse(BaseModel):
    items: list[VehicleResponse]
    total: int
    page: int
    page_size: int
    total_pages: int