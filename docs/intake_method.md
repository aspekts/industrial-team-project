# ADR — Realtime Log Intake Method

**Status:** Accepted  
**Date:** 2026-04-01  
**Owner:** Max (Parsers / Ingestion)

---

## Context

Issue #16 requires a live agent that simulates a production ATM edge device by continuously generating log entries, with the dashboard updating in near-real time. Issue #28 asks us to decide and document the intake method and record the trade-offs.

We needed to choose between:

| Approach | Description |
|---|---|
| **A — Polled file watch** | Agent writes log files; a watcher thread detects new content and triggers ingestion |
| **B — Queue/stream simulation** | Agent publishes to an in-process Kafka-like queue; a consumer reads and cleans records |
| **C — API push** | Agent POSTs new records to a Flask endpoint that persists them directly |
| **D — Direct DB micro-batch** | Agent writes records directly to the existing SQLite tables on a configurable timer, then re-runs detection |

---

## Decision

**Approach D — Direct DB micro-batch** was selected.

The agent (`src/synthetic/live_agent.py`) writes synthetic records directly into the already-cleaned source tables (`ATMA`, `ATMH`, `KAFK`, `TERM`, `WINOS`, `GCP`) in `atm_logs.db` on a configurable interval (default 10 seconds).  After each batch it calls `Detection.store_detections()` and `Correlator.store_incidents()` to update analysis tables.  The dashboard polls `/api/live-agent/status` every 5 seconds when the agent is active and refreshes all data panels on each poll.

---

## Rationale

1. **No extra moving parts.** The project already uses SQLite as the single source of truth. Approach A adds filesystem watchers; B adds a queue abstraction; C adds a new HTTP ingestion route with its own validation layer.  Approach D reuses the existing schema and analysis code with no new infrastructure.

2. **Matches local demo constraints.** SQLite handles concurrent readers well and is sufficient for a single-instance prototype. Flask's development server and SQLite both run in the same process, so there is no cross-process coordination overhead.

3. **Detection loop already exists.** `Detection` and `Correlator` are stateless classes that can be re-called on updated data. Approach A/B would require either re-running the full cleaning pass (wasteful) or a bespoke incremental path. Approach D calls only the two analysis stages that depend on new records.

4. **Controllable from the dashboard.** The agent is started, stopped, and injected from the Data flow screen via REST endpoints. This keeps the demo interactive without requiring a separate terminal process.

---

## Data flow

```
LiveAgent._tick()
  │
  ├── INSERT INTO ATMA, KAFK, ATMH  (always)
  ├── INSERT INTO TERM / GCP         (on A1, A4 injection)
  └── INSERT INTO WINOS              (always, anomalous on A6 injection)
        │
        └── Detection.store_detections()   → UPDATE analysis_detections
              │
              └── Correlator.store_incidents()  → UPDATE incidents
                    │
                    └── Dashboard polls /api/live-agent/status every 5 s
                          └── fetchDashboardData() refreshes all panels
```

---

## Latency and throughput assumptions

| Parameter | Value | Notes |
|---|---|---|
| Agent interval | 1–300 s (default 10 s) | Configurable via dashboard UI |
| Records per tick | 3–5 rows | ATMA + KAFK + ATMH always; TERM/GCP/WINOS conditional on injection |
| Detection re-run time | < 500 ms | Full SQL scan of existing + new rows on local SQLite |
| Dashboard refresh lag | ≤ 5 s after each batch | Bounded by poll interval |
| Sustained throughput | ~18–30 rows/min at default interval | Well within SQLite's write capacity |

---

## Failure modes and recovery

| Failure | Behaviour |
|---|---|
| Agent tick exception | Error is logged; agent continues on the next interval (`try/except` in `_run`) |
| Detection re-run fails | Error is logged; agent continues; stale detections remain until the next successful re-run |
| DB file locked by another process | SQLite raises `OperationalError`; caught by the tick's outer `try/except`; retried next interval |
| Flask server restart | Agent thread is daemon=True; it is killed with the process. Dashboard stop/start controls are used to resume |
| Agent never started | Dashboard shows "Idle" pill; all existing static data remains visible |

---

## Limitations and follow-up work

- **No persistence across restarts.** The agent state (events generated, injection queue) is in-memory. A persistent agent would require storing state in the DB or a sidecar file.
- **No true streaming pipeline.** Records bypass the full `LogCleaner` pass and are written with pre-validated values. For a production system, new log lines would flow through the parser → cleaner before reaching the analysis tables.
- **Single-node SQLite.** Concurrent writes from multiple agent threads would require WAL mode or a production database (PostgreSQL, etc.).
- **Stretch:** Replace the polling dashboard refresh with Server-Sent Events (SSE) or WebSocket push for sub-second latency.

---

## References

- `src/synthetic/live_agent.py` — LiveAgent implementation
- `src/dashboard/server.py` — `/api/live-agent/*` endpoints
- `src/analysis/detect.py` — Detection class called after each batch
- `src/analysis/correlate.py` — Correlator class called after each batch
- `src/cleaning/schemas.py` — Table schemas used for INSERT column order
