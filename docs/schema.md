# Shared Data Schema

> **Status: FROZEN as of Sprint 1, Day 4.**
> Changes after this point require a PR with approval from all team members.

---

## 1. Correlation ID Convention

Every event across all 7 sources carries a `correlation_id` that allows the analysis layer to link related events across sources.

**Format:** `<SOURCE_CODE>-<YYYYMMDD>-<UUID4>`

| Source | Source Code |
|---|---|
| ATM Application Log | `ATMA` |
| ATM Hardware Sensor Log | `ATMH` |
| Terminal Handler App Log | `TERM` |
| Kafka ATM Metrics Stream | `KAFK` |
| Prometheus Metrics | `PROM` |
| Windows OS Metrics Log | `WINOS` |
| GCP Cloud Metrics | `GCP` |

**Example:** `ATMA-20260317-f47ac10b-58cc-4372-a567-0e02b2c3d479`

When a single real-world event is observed across multiple sources (e.g. a network timeout visible in both ATM App and Kafka), all related log lines share the same UUID4 portion so the correlation engine can join them.

---

## 2. Universal Envelope Fields

Every record — regardless of source or format — must include these fields after parsing. The cleaning pipeline will validate their presence.

| Field | Type | Description | Example |
|---|---|---|---|
| `correlation_id` | `string` | Globally unique event ID (see §1) | `ATMA-20260317-f47ac10b-...` |
| `source` | `string` | Source code from §1 | `ATMA` |
| `timestamp` | `string (ISO 8601)` | UTC event time to millisecond precision | `2026-03-17T14:23:01.452Z` |
| `host_id` | `string` | Identifier of the machine/container/ATM | `atm-lon-042` |
| `anomaly_flag` | `boolean` | Set by analysis layer; `false` in raw data | `false` |
| `anomaly_type` | `string \| null` | A1–A7 or `null` if no anomaly detected | `A1` |

---

## 3. Per-Source Schemas

### 3.1 ATM Application Log (`ATMA`) — JSON

Emitted by the ATM application software on each transaction or system event.

| Field | Type | Nullable | Description |
|---|---|---|---|
| `correlation_id` | `string` | No | See §1 |
| `source` | `string` | No | `"ATMA"` |
| `timestamp` | `string` | No | ISO 8601 UTC |
| `host_id` | `string` | No | ATM machine ID |
| `transaction_id` | `string` | No | Unique per transaction |
| `event_type` | `string` | No | e.g. `WITHDRAWAL`, `BALANCE_QUERY`, `SESSION_START`, `ERROR` |
| `response_time_ms` | `integer` | No | End-to-end response time in ms |
| `status` | `string` | No | `SUCCESS`, `FAILURE`, `TIMEOUT` |
| `error_code` | `string` | Yes | Null unless `status` is `FAILURE` or `TIMEOUT` |
| `network_latency_ms` | `integer` | Yes | Populated for network-touching events |
| `anomaly_flag` | `boolean` | No | `false` in synthetic output |
| `anomaly_type` | `string` | Yes | `null` in synthetic output |

---

### 3.2 ATM Hardware Sensor Log (`ATMH`) — JSON

Emitted by hardware sensors monitoring physical ATM components.

| Field | Type | Nullable | Description |
|---|---|---|---|
| `correlation_id` | `string` | No | See §1 |
| `source` | `string` | No | `"ATMH"` |
| `timestamp` | `string` | No | ISO 8601 UTC |
| `host_id` | `string` | No | ATM machine ID |
| `component` | `string` | No | `CASH_CASSETTE`, `CARD_READER`, `RECEIPT_PRINTER`, `SCREEN` |
| `cassette_level_pct` | `float` | Yes | Percentage of cash remaining (0–100). Only for `CASH_CASSETTE` |
| `cassette_status` | `string` | Yes | `NORMAL`, `LOW`, `EMPTY`, `OUT_OF_SERVICE`. Only for `CASH_CASSETTE` |
| `sensor_value` | `float` | Yes | Generic sensor reading for non-cassette components |
| `sensor_unit` | `string` | Yes | Unit of `sensor_value` (e.g. `CELSIUS`, `RPM`) |
| `alert` | `boolean` | No | `true` if sensor reading crossed a threshold |
| `anomaly_flag` | `boolean` | No | `false` in synthetic output |
| `anomaly_type` | `string` | Yes | `null` in synthetic output |

---

### 3.3 Terminal Handler App Log (`TERM`) — JSON

Emitted by the Terminal Handler service that mediates between the ATM and the banking network.

| Field | Type | Nullable | Description |
|---|---|---|---|
| `correlation_id` | `string` | No | See §1 |
| `source` | `string` | No | `"TERM"` |
| `timestamp` | `string` | No | ISO 8601 UTC |
| `host_id` | `string` | No | Terminal Handler service instance ID |
| `session_id` | `string` | No | Banking network session identifier |
| `message_type` | `string` | No | `AUTHORISATION_REQUEST`, `AUTHORISATION_RESPONSE`, `SESSION_OPEN`, `SESSION_CLOSE`, `HEARTBEAT`, `ERROR` |
| `latency_ms` | `integer` | Yes | Round-trip latency to banking network |
| `status` | `string` | No | `SUCCESS`, `FAILURE`, `TIMEOUT` |
| `retry_count` | `integer` | No | Number of retries attempted (0 = first attempt succeeded) |
| `container_restart` | `boolean` | No | `true` if this event was the first after a container restart |
| `anomaly_flag` | `boolean` | No | `false` in synthetic output |
| `anomaly_type` | `string` | Yes | `null` in synthetic output |

---

### 3.4 Kafka ATM Metrics Stream (`KAFK`) — JSON

Events consumed from the Kafka topic that carries aggregated ATM metrics.

| Field | Type | Nullable | Description |
|---|---|---|---|
| `correlation_id` | `string` | No | See §1 |
| `source` | `string` | No | `"KAFK"` |
| `timestamp` | `string` | No | ISO 8601 UTC |
| `host_id` | `string` | No | Kafka producer (ATM) ID |
| `topic` | `string` | No | Kafka topic name |
| `partition` | `integer` | No | Kafka partition number |
| `offset` | `integer` | No | Kafka message offset |
| `event_sequence` | `integer` | No | Monotonically increasing per `host_id`; gaps or resets indicate A7 |
| `transaction_volume` | `integer` | No | Number of transactions in this window |
| `success_rate_pct` | `float` | No | Percentage of successful transactions (0–100) |
| `avg_response_time_ms` | `float` | No | Average response time across window |
| `anomaly_flag` | `boolean` | No | `false` in synthetic output |
| `anomaly_type` | `string` | Yes | `null` in synthetic output |

---

### 3.5 Prometheus Metrics (`PROM`) — CSV

Scraped time-series metrics from the JVM and application layer.

| Column | Type | Nullable | Description |
|---|---|---|---|
| `correlation_id` | `string` | No | See §1 |
| `source` | `string` | No | `PROM` |
| `timestamp` | `string` | No | ISO 8601 UTC |
| `host_id` | `string` | No | Service instance ID |
| `metric_name` | `string` | No | Prometheus metric name e.g. `jvm_memory_used_bytes` |
| `metric_value` | `float` | No | Current metric value |
| `metric_unit` | `string` | No | Unit string e.g. `bytes`, `seconds`, `ratio` |
| `label_job` | `string` | No | Prometheus `job` label |
| `label_instance` | `string` | No | Prometheus `instance` label |
| `anomaly_flag` | `boolean` | No | `false` in synthetic output |
| `anomaly_type` | `string` | Yes | `null` in synthetic output |

---

### 3.6 Windows OS Metrics Log (`WINOS`) — CSV

Periodic OS-level metrics collected from Windows hosts running ATM software.

| Column | Type | Nullable | Description |
|---|---|---|---|
| `correlation_id` | `string` | No | See §1 |
| `source` | `string` | No | `WINOS` |
| `timestamp` | `string` | No | ISO 8601 UTC |
| `host_id` | `string` | No | Windows hostname |
| `cpu_usage_pct` | `float` | No | CPU utilisation (0–100) |
| `memory_used_mb` | `float` | No | Physical memory used in MB |
| `memory_total_mb` | `float` | No | Total physical memory in MB |
| `memory_usage_pct` | `float` | No | `memory_used_mb / memory_total_mb * 100` |
| `disk_read_mbps` | `float` | No | Disk read throughput MB/s |
| `disk_write_mbps` | `float` | No | Disk write throughput MB/s |
| `page_faults_per_sec` | `float` | No | OS page fault rate |
| `anomaly_flag` | `boolean` | No | `false` in synthetic output |
| `anomaly_type` | `string` | Yes | `null` in synthetic output |

---

### 3.7 GCP Cloud Metrics (`GCP`) — CSV

Cloud-level metrics for containerised services running in Google Cloud Platform.

| Column | Type | Nullable | Description |
|---|---|---|---|
| `correlation_id` | `string` | No | See §1 |
| `source` | `string` | No | `GCP` |
| `timestamp` | `string` | No | ISO 8601 UTC |
| `host_id` | `string` | No | GCP container/instance name |
| `service_name` | `string` | No | GCP service identifier |
| `cpu_usage_pct` | `float` | No | Container CPU utilisation (0–100) |
| `memory_usage_pct` | `float` | No | Container memory utilisation (0–100) |
| `restart_count` | `integer` | No | Cumulative container restarts; increase indicates A4 |
| `network_in_mbps` | `float` | No | Inbound network MB/s |
| `network_out_mbps` | `float` | No | Outbound network MB/s |
| `anomaly_flag` | `boolean` | No | `false` in synthetic output |
| `anomaly_type` | `string` | Yes | `null` in synthetic output |

---

## 4. Anomaly Signatures Reference

Summarised here so the anomaly detection and synthetic data layers can agree on what to inject/detect.

| ID | Name | Primary Sources | Key Signals |
|---|---|---|---|
| A1 | Network timeout cascade | ATMA, KAFK, TERM | `status=TIMEOUT`, rising `network_latency_ms`, falling `success_rate_pct`, increasing `retry_count` |
| A2 | Cash cassette low → empty → OOS | ATMH, KAFK | `cassette_level_pct` declining, `cassette_status` stepping LOW→EMPTY→OUT_OF_SERVICE, transaction volume drops |
| A3 | JVM memory leak | PROM, GCP | `jvm_memory_used_bytes` rising monotonically without GC relief, `memory_usage_pct` climbing |
| A4 | Container restart loop | GCP, TERM | `restart_count` incrementing repeatedly, `container_restart=true` events in TERM |
| A5 | High response time + success rate drop | KAFK, ATMA | `avg_response_time_ms` spike, `success_rate_pct` drop in same window, `response_time_ms` outliers |
| A6 | OS memory pressure → app timeout | WINOS, ATMA | `memory_usage_pct` > 90, rising `page_faults_per_sec`, subsequent `status=TIMEOUT` in ATMA |
| A7 | Out-of-order / malformed Kafka event | KAFK | `event_sequence` gap or reset, malformed `timestamp` or missing required field |

---

## 5. File Naming Convention

| Type | Pattern | Example |
|---|---|---|
| Synthetic raw JSON | `data/synthetic/<SOURCE>_<YYYYMMDD>.json` | `data/synthetic/ATMA_20260317.json` |
| Synthetic raw CSV | `data/synthetic/<SOURCE>_<YYYYMMDD>.csv` | `data/synthetic/PROM_20260317.csv` |
| Cleaned output (Parquet) | `data/cleaned/<SOURCE>_<YYYYMMDD>.parquet` | `data/cleaned/ATMA_20260317.parquet` |

All paths are relative to the repository root.
