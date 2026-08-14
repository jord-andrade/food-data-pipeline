# Quality contract

## Blocking checks

| Check | Rule | Why it blocks |
|---|---|---|
| Food rows present | `count(food) > 0` | empty success is not a useful dataset |
| Observation rows present | `count(food_nutrient) > 0` | no nutritional evidence exists |
| Food key unique | one row per `fdc_id` | dimensions cannot be ambiguous |
| Observation key unique | one row per observation `id` | duplicate facts overstate evidence |
| Required food values | ID, description, publication date non-null | identifiers and lineage must be usable |
| Description content | non-whitespace | display and audit evidence must be legible |
| Food FK | every observation maps to a selected food | prevents detached facts |
| Category FK | every populated category maps to its dimension | preserves classification lineage |
| Recognized unit | unit belongs to the published USDA unit set | unit meaning must be explicit |
| Macro range | selected gram nutrients `<= 100 g/100 g` | catches unit/scale corruption |
| Energy range | energy `<= 1,000 kcal/100 g` | catches unit/scale corruption |
| Evidence coverage | every selected food has at least one observation | avoids empty dimensional members |

## Source warnings

| Warning | Handling |
|---|---|
| Nutrient foreign key missing | row is retained in quarantine with `missing_nutrient_dimension` |
| Amount missing | row is retained in quarantine with `missing_amount` |
| Amount negative | row is retained in quarantine with `negative_amount` |

When a row violates both warning conditions, `missing_amount` takes precedence because no numerical analytical value can be produced. The report still shows both source-level warning counts.

## Missing values

NutriTrace never fills a missing nutrient amount with zero. A zero means the source measured or declared zero; null means no accepted observation was available. Core-nutrient completeness is reported on the public page.
