from typing import Literal

from fastapi import Query
from pydantic import BaseModel, field_validator


class VehicleQueryParams(BaseModel):
    page: int = Query(
        default=1,
        ge=1,
    )

    page_size: int = Query(
        default=20,
        ge=1,
    )

    status: Literal["active", "inactive"] | None = Query(
        default=None,
    )

    search: str | None = Query(
        default=None,
        min_length=1,
    )

    sort_by: Literal[
        "plate",
        "brand",
        "model",
        "year",
        "capacity_kg",
        "status",
    ] = Query(
        default="plate",
    )

    order: Literal["asc", "desc"] = Query(
        default="asc",
    )

    @field_validator("page_size")
    @classmethod
    def limit_page_size(cls, value: int) -> int:
        return min(value, 100)

    @field_validator("search")
    @classmethod
    def clean_search(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError(
                "La búsqueda no puede estar vacía",
            )

        return cleaned_value