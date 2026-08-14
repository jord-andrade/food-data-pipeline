# Analytical data dictionary

All nutrient amounts represent USDA values per 100 g of food unless the source's nutrient definition states otherwise.

## `dim_food`

| Column | Type | Description |
|---|---|---|
| `fdc_id` | BIGINT | FoodData Central identifier; primary key |
| `description` | VARCHAR | USDA food description |
| `category_code` | VARCHAR | USDA food category code |
| `category` | VARCHAR | USDA food category description |
| `publication_date` | DATE | source publication date |

## `dim_nutrient`

| Column | Type | Description |
|---|---|---|
| `nutrient_id` | BIGINT | USDA nutrient identifier; primary key |
| `name` | VARCHAR | nutrient name |
| `unit_name` | VARCHAR | source measurement unit |
| `nutrient_nbr` | VARCHAR | USDA nutrient number |
| `rank` | DOUBLE | USDA display rank |

## `fact_food_nutrient`

| Column | Type | Description |
|---|---|---|
| `food_nutrient_id` | BIGINT | source observation identifier; primary key |
| `fdc_id` | BIGINT | foreign key to `dim_food` |
| `nutrient_id` | BIGINT | foreign key to `dim_nutrient` |
| `nutrient` | VARCHAR | denormalized nutrient label for convenience |
| `unit` | VARCHAR | denormalized unit for convenience |
| `amount` | DOUBLE | accepted source amount |
| `data_points` | BIGINT | number of source analytical data points when available |

## `food_nutrition_wide`

The food dimension columns plus nullable analytical columns:

- `energy_kcal`
- `protein_g`
- `fat_g`
- `carbohydrate_g`
- `fiber_g`
- `total_sugars_g`
- `calcium_mg`
- `iron_mg`
- `potassium_mg`
- `sodium_mg`

If more than one accepted observation exists for a food/nutrient pair, the wide layer uses the arithmetic mean while the long fact preserves each source observation.

## `quarantine_food_nutrient`

The projected source observation columns plus `rejection_reason`. Quarantine rows never enter `fact_food_nutrient` or the wide-layer aggregation.
