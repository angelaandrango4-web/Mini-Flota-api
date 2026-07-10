from datetime import datetime
import re
from typing import Literal

from pydantic import BaseModel, field_validator

class VehicleCreate(BaseModel):
    plate: str
    brand: str
    model: str
    year: int
    capacity_kg: float
    status: Literal["active", "inactive"]

    @field_validator("plate")
    @classmethod
    def validate_plate(cls, value: str) -> str:
        value = value.strip().upper()

        if not re.match(r"^[A-Z]{3}-\d{4}$", value):
            raise ValueError("La placa debe tener el formato AAA-1234")

        return value

    @field_validator("year")
    @classmethod
    def validate_year(cls, value: int) -> int:
        current_year = datetime.now().year
        if value < 1990 or value > current_year:
            raise ValueError(f"El año debe estar entre 1990 y {current_year}")
        return value


    @field_validator("capacity_kg")
    @classmethod
    def validate_capacity(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("La capacidad debe ser mayor que 0")
        return value
    

class VehicleResponse(BaseModel):
    id: str
    plate: str
    brand: str
    model: str
    year: int
    capacity_kg: float
    status: Literal["active", "inactive"]