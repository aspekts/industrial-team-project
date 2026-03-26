# Operations Hub Prototype

## Scope Alignment

To ensure the integrity of the dashboard, all features are strictly aligned with available data sources: `ATMA`, `ATMH`, `KAFK`, `PROM`, `GCP`, `TERM`, and `WINOS`.

Any previously implemented features that could not be supported by real data, including region tracking and SLA coverage, have been removed or stubbed out. The dashboard prioritises accurate, data-driven insights over unsupported or hardcoded functionality.

## Local Preview

To view the dashboard through Flask, run:

```bash
python3 -m src.dashboard.server
```

Then open `http://127.0.0.1:5000`.
