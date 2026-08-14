# Contributing

1. Open an issue for source-version, schema, or contract changes.
2. Create a focused branch from `main`.
3. Run `uv sync --frozen` and every command under “Quality gates” in the README.
4. Keep full/raw datasets outside Git.
5. Update provenance and the data dictionary with schema changes.
6. Open a pull request and explain any new source warnings or quarantined records.

Do not weaken a failing contract merely to make a release pass. Either fix pipeline logic or document, quarantine, and test a genuine source anomaly.
