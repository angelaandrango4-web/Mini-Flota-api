from pydantic import BaseModel, field_validator


class DriverCreate(BaseModel):
    name: str
    license: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("El nombre no puede estar vacío")

        return value

    @field_validator("license")
    @classmethod
    def validate_license(cls, value: str) -> str:
        value = value.strip().upper()

        if not value:
            raise ValueError("La licencia no puede estar vacía")

        return value


class DriverResponse(BaseModel):
    id: str
    name: str
    license: str