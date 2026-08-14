SELECT
    fdc_id,
    description,
    category,
    protein_g,
    energy_kcal,
    fiber_g
FROM food_nutrition_wide
WHERE protein_g IS NOT NULL
ORDER BY protein_g DESC
LIMIT 10;
