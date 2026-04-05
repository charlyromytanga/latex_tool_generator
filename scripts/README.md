# Scripts

This directory now contains only helper scripts that complement the unified CLI.

## Current Status

- `job_offer.txt`: sample raw offer text for end-to-end generation experiments.
- `run_api_container.sh`: build and run API container from `Dockerfile.api`.
- `run_unit_tests_container.sh`: build and run unit tests in `Dockerfile.test` container.
- `init_db.sh`: initialize the local SQLite schema.
- `init_postgres_db.sh`: initialize the PostgreSQL mirror schema.
- `mirror_sqlite_to_postgres.sh`: copy the local SQLite content into PostgreSQL.
- non-Python helper assets stay here; Python orchestration lives under `src/`.

## API Container

```bash
./scripts/run_api_container.sh
```

Options:

- `--no-build`: reuse existing Docker image.
- `--stop`: stop and remove existing API container before run.

## Unit Test Container

```bash
./scripts/run_unit_tests_container.sh
```

Options:

- `--no-build`: reuse existing Docker image.
- `--keep-container`: keep container after test run.

## Preferred Interface

```bash
uv sync
uv run cvrepo generate data/offers/2026/Q1/tier-1/switzerland/geneva/lombard_odier/offer_20260219_quant_dev_junior.md --language fr --archive
```

## PostgreSQL Mirror

Initialize PostgreSQL schema:

```bash
POSTGRES_DSN=postgresql://postgres:postgres@localhost:5432/recruitment_assistant bash scripts/init_postgres_db.sh
```

Mirror local SQLite data into PostgreSQL:

```bash
POSTGRES_DSN=postgresql://postgres:postgres@localhost:5432/recruitment_assistant bash scripts/mirror_sqlite_to_postgres.sh
```
