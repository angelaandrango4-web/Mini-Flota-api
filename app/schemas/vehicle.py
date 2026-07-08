from pydantic import BaseModel


class VehicleCreate(BaseModel):
    plate: str
    brand: str
    model: str
    year: int
    capacity_kg: float
    status: str


class VehicleResponse(BaseModel):
    id: str
    plate: str
    brand: str
    model: str
    year: int
    capacity_kg: float
    status: str