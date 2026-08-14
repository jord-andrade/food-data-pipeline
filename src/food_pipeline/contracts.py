from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

ALLOWED_UNITS = {
    "G",
    "IU",
    "KCAL",
    "MCG_RE",
    "MG",
    "MG_ATE",
    "MG_GAE",
    "PH",
    "SP_GR",
    "UG",
    "UMOL_TE",
    "kJ",
}


class FoodContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fdc_id: int = Field(gt=0)
    data_type: str = Field(min_length=1)
    description: str = Field(min_length=1)
    food_category_id: int | None = Field(default=None, gt=0)
    publication_date: date

    @field_validator("description")
    @classmethod
    def description_is_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("description must contain visible characters")
        return value.strip()


class NutrientContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int = Field(gt=0)
    name: str = Field(min_length=1)
    unit_name: str = Field(min_length=1)
    nutrient_nbr: str | None = None
    rank: float | None = Field(default=None, ge=0)

    @field_validator("unit_name")
    @classmethod
    def unit_is_supported(cls, value: str) -> str:
        if value not in ALLOWED_UNITS:
            raise ValueError(f"unsupported nutrient unit: {value}")
        return value


class FoodNutrientContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int = Field(gt=0)
    fdc_id: int = Field(gt=0)
    nutrient_id: int = Field(gt=0)
    amount: float | None = Field(default=None, ge=-1_000_000, le=1_000_000)
    data_points: int | None = Field(default=None, ge=0)


def validate_contract_rows(
    foods: list[dict[str, Any]],
    nutrients: list[dict[str, Any]],
    food_nutrients: list[dict[str, Any]],
) -> None:
    for row in foods:
        FoodContract.model_validate(row)
    for row in nutrients:
        NutrientContract.model_validate(row)
    for row in food_nutrients:
        FoodNutrientContract.model_validate(row)
