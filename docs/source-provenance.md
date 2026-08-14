# Source provenance

## Selected source

| Property | Value |
|---|---|
| Publisher | U.S. Department of Agriculture, Agricultural Research Service |
| Product | FoodData Central — Foundation Foods |
| Release | April 2026 (`2026-04-30`) |
| Format | CSV archive |
| Official catalog | <https://fdc.nal.usda.gov/download-datasets/> |
| Exact archive | <https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_foundation_food_csv_2026-04-30.zip> |
| SHA-256 | `d6d4f41dcd19a46abcdd67775379cb6f0292ff08daa7e0680fdd0982830bf57b` |
| Compressed size observed | approximately 3.7 MB |
| Extracted size stated by USDA | approximately 32 MB |
| Data terms | U.S. public domain / CC0 1.0 Universal |

The official download catalog listed April 2026 as the latest Foundation Foods release when this pipeline was authored on 2026-08-14. Updating to a later release is a code and contract change, not an automatic moving target.

## Why Foundation Foods

USDA describes Foundation Foods as analytically derived data and metadata for commodity or minimally processed foods, including information useful for understanding variability. It is compact enough for a reviewer to run locally while still exercising relational food, nutrient, category, and observation tables.

## Committed sample

The sample contains 20 fixed Foundation Food IDs selected for category diversity. The selection does not choose rows by nutrient value, which avoids tailoring the sample to a desired analytical result.

`data/sample/SOURCE.json` records the IDs, release, URL, checksum, license, and selection rule. `food.csv`, `food_nutrient.csv`, `nutrient.csv`, `food_category.csv`, and `foundation_food.csv` preserve the fields from the source download used by the pipeline.

## Updating the release

1. Review the new official download listing and documentation.
2. Change URL, release, directory name, and checksum together.
3. Download through `food-pipeline download`.
4. Rebuild the sample from the reviewed archive.
5. Run all contracts and inspect newly introduced warnings.
6. Update provenance, screenshot, and release notes in the same pull request.
