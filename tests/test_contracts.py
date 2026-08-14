from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from food_pipeline.contracts import FoodContract, FoodNutrientContract, NutrientContract


def test_food_contract_rejects_blank_descriptions() -> None:
    with pytest.raises(ValidationError, match="visible characters"):
        FoodContract(
            fdc_id=1,
            data_type="foundation_food",
            description="   ",
            food_category_id=1,
            publication_date=date(2026, 4, 30),
        )


def test_nutrient_contract_rejects_unknown_units() -> None:
    with pytest.raises(ValidationError, match="unsupported nutrient unit"):
        NutrientContract(id=1, name="Example", unit_name="OUNCE", nutrient_nbr="1", rank=1)


def test_observation_contract_rejects_extreme_amounts() -> None:
    with pytest.raises(ValidationError, match="greater than or equal to -1000000"):
        FoodNutrientContract(
            id=1,
            fdc_id=1,
            nutrient_id=1003,
            amount=-1_000_001,
            data_points=1,
        )
