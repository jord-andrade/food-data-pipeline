# Architecture

## Design goal

A clean clone should produce the same validated analytical shape without storing the 32 MB extracted USDA release in Git. The committed sample exercises the identical path used by the full release.

## Boundaries

| Module | Responsibility |
|---|---|
| `config.py` | pinned release URL, SHA-256, required tables, and core nutrient mapping |
| `download.py` | HTTPS acquisition, checksum verification, safe ZIP extraction |
| `sample.py` | deterministic 20-food subset derived from fixed FDC identifiers |
| `source.py` | projected CSV reads, type normalization, Foundation Food filtering |
| `contracts.py` | row contracts for food, nutrient, and observation records |
| `quality.py` | primary key, foreign key, null, unit, range, and coverage evidence |
| `transform.py` | dimensions, long fact, wide profile, quarantine, Parquet, DuckDB, hashes |
| `report.py` | deterministic JSON and static HTML evidence |
| `pipeline.py` | fail-closed orchestration |
| `cli.py` | public `download`, `build-sample`, and `run` commands |

## Failure model

The pipeline separates three outcomes:

- **blocking failure:** pipeline-controlled contracts such as duplicate keys, negative amounts, invalid categories, unsafe archives, or implausible macro/energy values stop publication;
- **source warning:** known source incompleteness remains visible and the affected row is quarantined;
- **valid row:** the observation enters the fact and may contribute to the wide profile.

`quality-report.json` is written before a blocking exception is raised, so failed runs still leave diagnosable evidence. Analytical outputs are written only after blocking checks pass.

## Storage model

```text
dim_food 1 ──────── * fact_food_nutrient * ──────── 1 dim_nutrient
   │
   └────────────── 1 food_nutrition_wide

quarantine_food_nutrient  (rejected source observations + reason)
```

Parquet is the portable interchange layer. DuckDB packages every table into one local analytical database and adds indexes on the long fact's food and nutrient keys. The wide table makes common comparisons convenient without discarding the long-form lineage.

## Determinism

- exact source URL and release date;
- pinned source SHA-256;
- fixed sample FDC identifiers;
- stable numeric sorting before writes;
- fixed schema projections;
- no wall-clock timestamp in generated reports;
- frozen Python dependency graph (`uv.lock`);
- CI regenerates `site/` and fails on a Git diff.

## Security

- only the pinned HTTPS USDA URL is used;
- a checksum mismatch fails before extraction;
- every ZIP path is resolved against the destination to prevent traversal;
- no API key is required or accepted;
- SQL table names are internal constants, while file paths are bound parameters;
- raw/full data and environment files are ignored.
