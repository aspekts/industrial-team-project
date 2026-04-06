# NCR Atleos Log Aggregation, Analysis and Diagnostics Platform

University of Dundee Industrial Team Project, 2026.

This repository contains a prototype observability platform for ATM operations. It ingests synthetic logs from multiple banking and infrastructure sources, validates and cleans them into SQLite, detects known anomaly patterns, scores unusual behaviour with Isolation Forest, correlates related detections into incidents, and presents the results in a role-based dashboard backed by a documented Flask API.

## What The Repo Covers

- Synthetic data generation for seven source systems
- Parser and ingestion flow from source files into raw text exports
- Data cleaning and schema-based loading into SQLite
- Rules-based anomaly detection for A1-A7 patterns
- ML-based anomaly scoring for selected metric sources
- Cross-source incident correlation
- Recommendation generation and feedback capture
- Role-based dashboard with auth, action logging, and live simulation controls
- Swagger-powered API documentation for the Flask backend
- Tests covering parsers, cleaning, analysis, ML, and dashboard endpoints

## End-To-End Flow

```text
Synthetic source files
  -> src/parsers/ingest.py
  -> data/raw/*.txt
  -> src/cleaning/data_cleaning.py
  -> data/clean/atm_logs.db
  -> src/analysis/detect.py
  -> analysis_detections
  -> src/ml/scorer.py
  -> ml_anomaly_scores
  -> src/analysis/correlate.py
  -> incidents
  -> src/dashboard/server.py
  -> HTML dashboard + REST API + Swagger docs
```

The main application entrypoint is `main.py`. It starts the Flask dashboard and runs the ingestion, cleaning, detection, scoring, and correlation pipeline.

## Repository Overview

### Main entrypoints

- `main.py`: starts the dashboard server and runs the pipeline
- `src/dashboard/server.py`: Flask application, HTML views, API endpoints, Swagger docs
- `src/synthetic/live_agent.py`: background synthetic event generator for near-real-time demo updates

### Source modules

- `src/parsers/`: converts synthetic source files into raw tabular exports
- `src/cleaning/`: validates, normalises, and loads data into SQLite
- `src/analysis/`: static anomaly detection, taxonomy, correlation, recommendations
- `src/ml/`: feature extraction, Isolation Forest model, anomaly scoring
- `src/dashboard/`: backend routes, auth, templates, and frontend assets
- `src/synthetic/`: synthetic data generation and live injection logic

### Supporting directories

- `data/synthetic/`: committed synthetic source data used for demo and testing
- `data/raw/`: parser output generated locally
- `data/clean/`: cleaned SQLite databases and related outputs
- `docs/`: schema documentation and architecture decisions
- `tests/`: automated test suite mirroring the main project areas

## Data Sources

The platform currently models seven synthetic data sources:

| Source | Table | Format | Purpose |
|---|---|---|---|
| ATM Application Log | `ATMA` | JSON | ATM client activity, errors, request lifecycle |
| ATM Hardware Sensor Log | `ATMH` | JSON | Hardware status, sensor warnings, cash cassette state |
| Terminal Handler App Log | `TERM` | JSON | Service-side request handling and runtime failures |
| Kafka ATM Metrics Stream | `KAFK` | JSON | Transaction throughput, success rates, and failures |
| Prometheus Metrics | `PROM` | CSV | JVM and service metrics |
| Windows OS Metrics | `WINOS` | CSV | ATM host CPU, memory, disk, and network telemetry |
| GCP Cloud Metrics | `GCP` | CSV | Infrastructure and container-level cloud metrics |

The shared schema reference lives in `docs/schema.md`.

## Anomaly Coverage

The rules-based analysis layer currently models these anomaly types:

| ID | Name | Primary Sources |
|---|---|---|
| A1 | Network timeout cascade | ATMA, KAFK, TERM |
| A2 | Cash cassette depletion | ATMH, KAFK |
| A3 | JVM memory leak -> OOM | PROM, GCP, TERM |
| A4 | Container restart loop | GCP, TERM |
| A5 | Performance degradation | KAFK, ATMA |
| A6 | OS memory pressure | WINOS, ATMA |
| A7 | Out-of-order or malformed Kafka event | KAFK |

Static taxonomy data is managed through `src/analysis/taxonomy.py`.

## Dashboard Capabilities

The dashboard is served by Flask and supports three user roles:

- `admin`: platform-wide readiness, governance, and source coverage
- `manager`: operational queue, issue review, and action follow-up
- `ops`: ATM-level incidents, technical evidence, and live operational monitoring

Key dashboard features:

- session-based signup and login
- role-specific dashboard routing
- health and system status endpoints
- ATM list, alerts, incidents, trends, taxonomy, ML summary, and recommendations
- feedback capture for recommendation quality
- action logging for manager and ops workflows
- live agent start, stop, status, and anomaly injection controls

## API Documentation

Swagger UI is integrated into the Flask app.

- Swagger UI: `/api/docs/`
- OpenAPI JSON: `/api/openapi.json`

Once the app is running locally, open:

- `http://127.0.0.1:5000/api/docs/`

The docs are generated from route docstrings in `src/dashboard/server.py`.

## Live Agent

The live agent provides a near-real-time demo mode for the dashboard.

- it runs as a background thread
- it writes directly into the cleaned SQLite tables
- it re-runs detection and correlation after each tick
- it can inject selected anomaly types for demo scenarios

Supported injection types currently include `A1`, `A2`, `A4`, `A5`, `A6`, and `A7`.

The design decision and trade-offs are documented in `docs/intake_method.md`.

## Recommendation Engine

`src/analysis/recommendations.py` provides a rule-driven recommendation layer that:

- maps anomaly types to remediation guidance
- ranks recommendations with a confidence score
- stores user feedback in SQLite
- adjusts recommendation confidence using recorded likes and dislikes

## Machine Learning Layer

`src/ml/scorer.py` orchestrates feature extraction and Isolation Forest scoring for:

- `KAFK`
- `WINOS`
- `GCP`
- `PROM`

The ML layer stores results in `ml_anomaly_scores` and can register dynamic taxonomy entries for detected anomaly clusters.

## Setup

### Prerequisites

- Python 3.11+
- a local virtual environment

### Recommended local setup

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
```

This repository already expects a project-local virtual environment at `.venv`.

## Running The Project

### Start the full application

```bash
.venv/bin/python main.py
```

By default the app starts on `http://0.0.0.0:5000` using values from `config.ini`.

### Important runtime paths

- raw parser output: `data/raw`
- cleaned database: `data/clean/atm_logs.db`
- auth database: `data/clean/auth.db`
- cleaning error output: `data/clean/broken_logs.json`

### Configuration

`config.ini` currently defines:

```ini
[NETWORK]
port=5000
host=0.0.0.0

[PATHS]
raw_data_dir=data/raw
cleaned_db_path=data/clean/atm_logs.db
error_path=data/clean
```

### Alternative dashboard-only startup

```bash
.venv/bin/python src/dashboard/server.py
```

This starts the Flask app directly, without the full pipeline orchestration performed by `main.py`.

## Development Commands

### Install dependencies

```bash
.venv/bin/pip install -r requirements.txt
```

### Run tests

```bash
.venv/bin/pytest
```

### Run linting

```bash
.venv/bin/ruff check .
```

### Open the API docs after startup

```text
http://127.0.0.1:5000/api/docs/
```

## Test Coverage Areas

The current test suite includes coverage for:

- parser ingestion in `tests/parsers/`
- cleaning and filtering in `tests/cleaning/`
- taxonomy and incident correlation in `tests/analysis/`
- Isolation Forest scoring in `tests/ml/`
- dashboard action and documentation endpoints in `tests/dashboard/`
- scaffold checks in `tests/test_scaffold.py`

## Deployment Notes

The repository includes a `railway.toml` deployment config.

- start command: `python main.py`
- health check path: `/health`

## Architecture References

- `docs/schema.md`: shared schema and anomaly signature reference
- `docs/intake_method.md`: ADR for the real-time ingestion approach

## Team Ownership

| Name | Area |
|---|---|
| Marcus | Lead, synthetic data generation, ML model, recommendation engine |
| Max | Log parsers and ingestion for all seven sources |
| Emily | Data filtering |
| Olga | Data cleaning pipeline |
| Callum | Rules-based anomaly detection and cross-source correlation |
| Sophina | Dashboard and visualisation |

## Contributing

1. Branch from `main` using `<initials>/<issue-number>-<short-description>`.
2. Open a pull request linked to the relevant issue.
3. Get at least one teammate review before merging.
4. Ensure linting and tests pass.

Schema changes are controlled through `docs/schema.md` and should only be updated through reviewed pull requests with agreement from affected owners.
