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
        value = value.strip()

        if not value.isdigit():
            raise ValueError(
                "La licencia debe contener únicamente números",
            )

        if len(value) != 10:
            raise ValueError(
                "La licencia debe contener exactamente 10 dígitos",
            )

        return value


class DriverResponse(BaseModel):
    id: str
    name: str
    license: str