# NCR Atleos — Log Aggregation, Analysis & Diagnostics Platform

> University of Dundee · Industrial Team Project · 2026

A prototype observability platform that ingests logs from multiple ATM and banking infrastructure sources, detects anomalies, and surfaces intelligent diagnostic recommendations.

---

## Team

| Name | Role |
|---|---|
| Marcus | Lead · Synthetic data generation · ML model · Recommendation engine |
| Max | Log parsers (all 7 sources) |
| Emily | Data filtering |
| Olga | Data cleaning pipeline |
| Callum | Anomaly detection rules · Cross-source correlation |
| Sophina | Dashboard & visualisation |

---

## Data Sources

| # | Source | Format |
|---|---|---|
| 1 | ATM Application Log | JSON |
| 2 | ATM Hardware Sensor Log | JSON |
| 3 | Terminal Handler Application Log | JSON |
| 4 | Kafka ATM Metrics Stream | JSON |
| 5 | Prometheus Metrics | CSV |
| 6 | Windows OS Metrics Log | CSV |
| 7 | GCP Cloud Metrics | CSV |

All data used in this project is **synthetic** — no real NCR Atleos production data is included in this repository.

---

## Anomaly Types

| ID | Name | Primary Sources |
|---|---|---|
| A1 | Network timeout cascade | ATM App, Kafka, Terminal Handler |
| A2 | Cash cassette low → empty → OOS | ATM Hardware, Kafka |
| A3 | JVM memory leak | Prometheus, GCP |
| A4 | Container restart loop | GCP, Terminal Handler |
| A5 | High response time + success rate drop | Kafka, ATM App |
| A6 | OS memory pressure → app timeout | Windows OS, ATM App |
| A7 | Out-of-order / malformed Kafka event | Kafka |

---

## Project Structure

```
.
├── data/
│   ├── synthetic/      # Generated log samples (committed for dev/test use)
│   ├── raw/            # Parser output — gitignored, generated locally
│   └── cleaned/        # Cleaned pipeline output — gitignored, generated locally
├── src/
│   ├── parsers/        # Max — log ingestion & parsing for all 7 sources
│   ├── cleaning/       # Emily & Olga — normalisation, deduplication, null handling
│   ├── analysis/       # Callum — anomaly detection rules (A1-A7) & correlation engine
│   ├── ml/             # Marcus — Isolation Forest model & recommendation engine
│   └── dashboard/      # Sophina — visualisation & UI
├── tests/              # Mirrors src/ structure
├── docs/               # Schema spec, architecture diagrams, ADRs
├── notebooks/          # Exploratory / prototyping notebooks (not production code)
└── .github/workflows/  # CI — lint + test on every push / PR
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- `pip` or a virtual environment manager (e.g. `uv`, `venv`)

### Setup

```bash
git clone https://github.com/aspekts/industrial-team-project.git
cd industrial-team-project

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### Running pipeline

```bash
python main.py
```

### Running tests

```bash
pytest
```

### Linting

```bash
ruff check .
```

---

## Sprint Plan

| Sprint | Days | Goal | Milestone |
|---|---|---|---|
| Sprint 1 — Foundation | 1–7 | Schema, synthetic data, parsers, cleaning pipeline, static wireframes | Mar 22 |
| Sprint 2 — Core Features | 8–16 | Anomaly detection, ML model, correlation engine, working dashboard | Mar 31 |
| Sprint 3 — Polish & Stretch | 17–21 | Recommendation engine, feedback loop, stretch goals, final docs | Apr 5 |

---

## ATM Operations Dashboard
Overview

This project is an operations dashboard designed to monitor ATM systems across multiple data sources, including application logs, hardware sensors, streaming metrics, and infrastructure telemetry.

The dashboard is built to support different user personas (e.g. Admin, ATM Manager, Operations) and provides a structured view of system activity, errors, and operational status.

Features
Role-based access (Admin, Manager, Ops)
Persona-specific dashboards
Flask backend serving dashboard and API endpoints
Integration-ready for live data from SQLite (atm_logs.db)
Health and system status endpoints
Clean, structured UI for operational monitoring
Project Structure
src/
  dashboard/
    server.py        # Flask backend
    index.html       # Dashboard UI
    styles.css       # Styling
    app.js           # Frontend logic

data/
  clean/
    atm_logs.db      # Cleaned database (if available)
Running the Application
1. Start the Flask server
python src/dashboard/server.py
2. Open in browser
http://127.0.0.1:5000

This will take you to the login page.

Authentication Flow
Users can sign up and choose a role:
Admin
ATM Manager
Operations
Users can then sign in using their credentials
After login, users are redirected to their role-specific dashboard
Sessions are managed using Flask
Logout clears the session and returns to the login page
API Endpoints
Health Check
/health

Returns system status and database availability.

API Status
/api/status

Returns:

whether the database is present
available tables (if database exists)
Data Integration

The dashboard is designed to integrate with a cleaned SQLite database:

data/clean/atm_logs.db

If the database is not present:

the system will still run
endpoints will safely return empty/unavailable states
User Personas
Admin
Full system overview
Cross-source visibility
High-level monitoring
ATM Manager
Local ATM status
Immediate operational issues
Action-focused information
Operations (Ops)
Infrastructure health
Error spikes and system failures
Telemetry and backend monitoring
Notes
The authentication system is implemented using Flask sessions
Passwords are securely stored using hashing

---

## Contributing

1. Branch off `main` using the naming convention `<initials>/<issue-number>-<short-description>`
   (e.g. `mc/4-synthetic-data`).
2. Open a PR referencing the issue number.
3. At least one teammate must review before merging.
4. CI (lint + tests) must pass.

> **Schema freeze:** The shared data schema (`docs/schema.md`) is frozen after Day 4 and may only
> be changed via PR with consensus from all affected owners.


The system is designed to be lightweight and extendable
Some features may depend on data availability from the pipeline
