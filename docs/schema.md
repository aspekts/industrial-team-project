# Shared Data Schema

> **Status: FROZEN as of Sprint 1, Day 4.**
> Changes after this point require a PR with approval from all team members.
>
> **Source of truth:** NCR Atleos data dictionaries in `Assets/Data Dictionary/`.
> This document is a summary reference — always consult the data dictionaries for
> the normative field definitions.

---

## 1. Cross-Source Correlation

Four fields link related events across sources for the same real-world transaction:

| Field | Type | Shared by | Notes |
|---|---|---|---|
| `correlation_id` | UUID v4 | ATMA, ATMH, TERM, KAFK | Same UUID for all log lines belonging to one transaction. Null for non-transaction events |
| `transaction_id` | UUID v4 | ATMA, TERM, KAFK | Unique per banking transaction |
| `atm_id` | string | ATMA, ATMH, TERM, KAFK, WINOS | Format `ATM-[A-Z]{2}-[0-9]{4}`, e.g. `ATM-GB-0042` |
| `timestamp` | ISO 8601 UTC | All 7 sources | Must be monotonically increasing per source. Millisecond precision |

> **Note on `correlation_id`:** This is a plain UUID v4, not prefixed with a source
> code. The same UUID appears across ATMA, ATMH, TERM, and KAFK for the same
> transaction, enabling the correlation engine to join them.

**The `_anomaly` field** appears in synthetic data files as an internal validation
tag (`null` for clean records, `"A1"`-`"A7"` for injected anomalies). It is **not**
part of the schema and will not be present in real production logs.

---

## 2. Per-Source Schemas

### 2.1 ATM Application Log (`ATMA`) — JSON

C# ATM client application running on Windows. Event-driven.

| Field | Type | Nullable | Notes |
|---|---|---|---|
| `timestamp` | ISO 8601 | No | UTC, millisecond precision |
| `log_level` | enum | No | `TRACE` `DEBUG` `INFO` `WARN` `ERROR` `FATAL` |
| `atm_id` | string | No | `ATM-[A-Z]{2}-[0-9]{4}` |
| `location_code` | string | No | `LOC-[0-9]{4}` |
| `session_id` | UUID v4 | Yes | Null if no active user session |
| `correlation_id` | UUID v4 | Yes | Null for non-transaction events |
| `transaction_id` | UUID v4 | Yes | Null for non-transaction events |
| `event_type` | enum | No | `STARTUP` `SHUTDOWN` `CARD_INSERTED` `CARD_EJECTED` `PIN_ENTERED` `TRANSACTION_START` `TRANSACTION_END` `CASH_DISPENSED` `RECEIPT_PRINTED` `NETWORK_CONNECT` `NETWORK_DISCONNECT` `HARDWARE_FAULT` `SUPERVISOR_MODE_ENTER` `SUPERVISOR_MODE_EXIT` `JOURNAL_WRITE` `TIMEOUT` `MALFORMED_REQUEST` `UNKNOWN` |
| `message` | string | No | Human-readable log message. Max 512 chars |
| `component` | string | No | Software module, e.g. `CashDispenser`, `TransactionManager` |
| `thread_id` | integer | Yes | OS thread ID |
| `response_time_ms` | integer | Yes | Null for non-timed events |
| `error_code` | string | Yes | Pattern `ERR-[0-9]{4}`. Null if no error |
| `error_detail` | string | Yes | Stack trace / detail. Max 1024 chars. Null if no error |
| `atm_status` | enum | No | `Online` `Offline` `In Service` `In Supervisor` `Out of Service` |
| `os_version` | string | Yes | e.g. `Windows 10 LTSB 2016` |
| `app_version` | string | No | e.g. `3.4.1-build.209` |

---

### 2.2 ATM Hardware Sensor Log (`ATMH`) — JSON

Hardware health and sensor events from ATM peripherals. Event-driven.

| Field | Type | Nullable | Notes |
|---|---|---|---|
| `timestamp` | ISO 8601 | No | UTC |
| `atm_id` | string | No | Matches ATMA `atm_id` |
| `correlation_id` | UUID v4 | Yes | Set when hardware event is linked to a transaction |
| `component` | enum | No | `CASH_DISPENSER` `CARD_READER` `RECEIPT_PRINTER` `KEYPAD` `SCREEN` `CAMERA` `UPS` `NETWORK_ADAPTER` `DOOR_SENSOR` `TEMPERATURE_SENSOR` |
| `event_type` | enum | No | `STATUS_OK` `WARNING` `FAULT` `SELF_TEST_PASS` `SELF_TEST_FAIL` `CASSETTE_LOW` `CASSETTE_EMPTY` `JAM_DETECTED` `JAM_CLEARED` `DOOR_OPEN` `DOOR_CLOSED` `TEMPERATURE_HIGH` `TEMPERATURE_NORMAL` `POWER_RESTORED` `POWER_FAILURE` |
| `severity` | enum | No | `INFO` `WARNING` `CRITICAL` |
| `message` | string | No | Human-readable description. Max 256 chars |
| `metric_name` | string | Yes | e.g. `cassette_note_count`, `internal_temp_celsius` |
| `metric_value` | number | Yes | Numeric metric reading |
| `metric_unit` | string | Yes | e.g. `notes`, `celsius`, `volts` |
| `threshold_value` | number | Yes | Threshold that triggered WARNING/CRITICAL |
| `firmware_version` | string | Yes | e.g. `FW-2.1.4` |

> **A2 signal:** `event_type` steps `CASSETTE_LOW` -> `CASSETTE_EMPTY` on
> `component=CASH_DISPENSER`, with `metric_name=cassette_note_count` declining.

---

### 2.3 Terminal Handler Application Log (`TERM`) — JSON

Java-based Terminal Handler service running in Docker on GCP. Structured logging via SLF4J/Logback.

| Field | Type | Nullable | Notes |
|---|---|---|---|
| `timestamp` | ISO 8601 | No | UTC |
| `log_level` | enum | No | `TRACE` `DEBUG` `INFO` `WARN` `ERROR` `FATAL` |
| `service_name` | string | No | `terminal-handler` |
| `service_version` | string | No | e.g. `2.7.0-SNAPSHOT` |
| `container_id` | string | Yes | Short Docker container ID, 12 hex chars |
| `pod_name` | string | Yes | GCP/Kubernetes pod name |
| `correlation_id` | UUID v4 | Yes | Shared with originating ATM event |
| `transaction_id` | UUID v4 | Yes | Banking transaction ID |
| `atm_id` | string | Yes | Originating ATM. Null for non-ATM events |
| `event_type` | enum | No | `REQUEST_RECEIVED` `REQUEST_FORWARDED` `RESPONSE_SENT` `AUTH_SUCCESS` `AUTH_FAILURE` `DB_QUERY` `DB_ERROR` `KAFKA_PUBLISH` `KAFKA_CONSUME` `NETWORK_TIMEOUT` `HEALTH_CHECK` `STARTUP` `SHUTDOWN` `EXCEPTION` `UNKNOWN` |
| `message` | string | No | Human-readable log message. Max 1024 chars |
| `logger_name` | string | Yes | Fully qualified Java class, e.g. `com.synthbank.terminalhandler.TransactionService` |
| `thread_name` | string | Yes | JVM thread name, e.g. `http-nio-8080-exec-3` |
| `response_time_ms` | integer | Yes | End-to-end request processing time. Null for non-request events |
| `http_status_code` | integer | Yes | HTTP status code. Null if not applicable |
| `exception_class` | string | Yes | Java exception class name. Null if no exception |
| `exception_message` | string | Yes | Exception message + partial stack trace. Max 2048 chars |
| `db_query_time_ms` | integer | Yes | DB query execution time. Null if no DB operation |
| `environment` | enum | No | `dev` `staging` `prod-sim` |

> **A4 signal:** `event_type=STARTUP` repeated in short succession with changing
> `container_id` values; `FATAL` events with `exception_class=OutOfMemoryError`.

---

### 2.4 Kafka ATM Metrics Stream (`KAFK`) — JSON

Published by Terminal Handler each minute per ATM. Kafka topic: `atm-metrics`.

| Field | Type | Nullable | Notes |
|---|---|---|---|
| `timestamp` | ISO 8601 | No | UTC — when metric snapshot was published |
| `event_id` | UUID v4 | No | Unique per Kafka message |
| `correlation_id` | UUID v4 | Yes | Links to ATM App Log / Terminal Handler for same transaction window |
| `atm_id` | string | No | ATM that produced the metrics; also used as Kafka message key |
| `atm_status` | enum | No | `Online` `Offline` `In Service` `In Supervisor` `Out of Service` |
| `transaction_rate_tps` | number | No | Transactions per second in current window |
| `response_time_ms` | integer | No | Average response time across window (ms) |
| `transaction_volume` | integer | No | Cumulative transaction count since last reset |
| `transaction_success_rate` | number | No | Percentage of successful transactions (0-100) |
| `transaction_failure_reason` | enum | No | `NONE` `NETWORK_TIMEOUT` `HOST_UNAVAILABLE` `CARD_DECLINED` `INSUFFICIENT_FUNDS` `INVALID_PIN` `CASH_DISPENSE_ERROR` `CARD_JAM` `SESSION_TIMEOUT` `MALFORMED_REQUEST` `UNKNOWN_ERROR` |
| `failure_count` | integer | No | Failed transactions in this window |
| `window_duration_seconds` | integer | No | Aggregation window duration |
| `kafka_partition` | integer | Yes | Kafka partition |
| `kafka_offset` | integer | Yes | Kafka offset |

> **A7 signal:** Timestamp not monotonic vs. previous offset, or `atm_status=null`
> / missing required fields (schema validation failure).

---

### 2.5 Prometheus Metrics (`PROM`) — CSV

Scraped from Terminal Handler Java app `/metrics` endpoint every 15 seconds.

| Column | Type | Nullable | Notes |
|---|---|---|---|
| `timestamp` | ISO 8601 | No | UTC scrape time |
| `metric_name` | string | No | Prometheus snake_case name, e.g. `jvm_memory_used_bytes` |
| `metric_type` | enum | No | `counter` `gauge` `histogram` `summary` `untyped` |
| `metric_value` | number | No | Metric sample value |
| `service_name` | string | No | Service exposing the metric, e.g. `terminal-handler` |
| `pod_name` | string | Yes | Kubernetes pod name |
| `container_id` | string | Yes | Docker container short ID |
| `label_area` | string | Yes | Prometheus `area` label (e.g. `heap`, `nonheap`) |
| `label_env` | string | Yes | Prometheus `env` label |
| `help_text` | string | Yes | Prometheus HELP descriptor |

**Key metrics:** `jvm_memory_used_bytes`, `jvm_memory_max_bytes`, `jvm_gc_pause_seconds_sum`, `process_cpu_usage`, `http_server_requests_seconds_count`, `kafka_producer_record_error_total`, `db_connection_pool_active`

> **A3 signal:** `jvm_memory_used_bytes` rising monotonically (300 MB -> ~1 GB+)
> with `jvm_gc_pause_seconds_sum` increasing (GC thrashing).

---

### 2.6 Windows OS Metrics (`WINOS`) — CSV

OS-level metrics from Windows hosts running ATM software. Collected every 60 seconds.

| Column | Type | Nullable | Notes |
|---|---|---|---|
| `timestamp` | ISO 8601 | No | UTC collection time |
| `atm_id` | string | No | Matches `atm_id` on other sources |
| `hostname` | string | No | Windows hostname, e.g. `ATM-HOST-0042` |
| `os_version` | string | Yes | e.g. `Windows 10 LTSB 2016 Build 14393` |
| `cpu_usage_percent` | number | No | Total CPU utilisation (0-100) |
| `memory_used_mb` | number | No | Physical RAM in use (MB) |
| `memory_total_mb` | number | No | Total physical RAM (MB) |
| `memory_usage_percent` | number | Yes | Derived: `memory_used_mb / memory_total_mb * 100` |
| `disk_read_bytes_per_sec` | number | Yes | Disk read throughput (bytes/s) |
| `disk_write_bytes_per_sec` | number | Yes | Disk write throughput (bytes/s) |
| `disk_free_gb` | number | No | Free disk space on primary volume (GB) |
| `network_bytes_sent_per_sec` | number | Yes | Outbound network throughput (bytes/s) |
| `network_bytes_recv_per_sec` | number | Yes | Inbound network throughput (bytes/s) |
| `network_errors` | integer | Yes | Network interface error count since last collection |
| `process_count` | integer | Yes | Total active OS processes |
| `system_uptime_seconds` | integer | Yes | Seconds since last OS boot |
| `event_log_errors_last_min` | integer | Yes | Windows Event Log ERROR entries in last minute |

> **A6 signal:** `memory_usage_percent` escalating toward 100%, `network_errors`
> growing, `cpu_usage_percent` rising. Followed by `TIMEOUT` events in ATMA.

---

### 2.7 GCP Cloud Metrics (`GCP`) — CSV

Infrastructure metrics for VM instances and containers hosting Terminal Handler. Collected every 60 seconds.

| Column | Type | Nullable | Notes |
|---|---|---|---|
| `timestamp` | ISO 8601 | No | UTC sample time |
| `project_id` | string | No | GCP project ID, e.g. `synth-banking-sim-001` |
| `resource_type` | enum | No | `gce_instance` `gke_container` `cloud_sql_instance` |
| `resource_id` | string | No | Pod name, instance name, or SQL instance |
| `zone` | string | Yes | GCP zone, e.g. `europe-west2-b` |
| `metric_name` | string | No | GCP metric path, e.g. `container/cpu/usage_time` |
| `metric_value` | number | No | Metric sample value |
| `metric_unit` | string | Yes | GCP Metrics unit notation, e.g. `s{CPU}` |
| `cpu_usage_percent` | number | Yes | Container/VM CPU utilisation (0-100) |
| `memory_usage_bytes` | integer | Yes | Memory consumed by container (bytes) |
| `memory_limit_bytes` | integer | Yes | Memory limit assigned to container (bytes) |
| `network_ingress_bytes` | integer | Yes | Network bytes received in interval |
| `network_egress_bytes` | integer | Yes | Network bytes sent in interval |
| `restart_count` | integer | Yes | Cumulative container restarts |
| `label_app` | string | Yes | GCP label `app` |
| `label_env` | string | Yes | GCP label `env` |
| `label_version` | string | Yes | GCP label `version` |

> **A3 signal:** `memory_usage_bytes` climbing alongside Prometheus JVM heap.
> **A4 signal:** `restart_count` incrementing; matches TERM `container_id` changes.

---

## 3. Anomaly Signatures Reference

| ID | Name | Primary Sources | Key Signals |
|---|---|---|---|
| A1 | Network timeout cascade | ATMA, KAFK, TERM | ATMA `event_type=NETWORK_DISCONNECT`->`TIMEOUT`; KAFK `atm_status=Offline`, `transaction_failure_reason=HOST_UNAVAILABLE`; TERM `event_type=NETWORK_TIMEOUT` |
| A2 | Cash cassette depletion -> OOS | ATMH, KAFK | ATMH `event_type` steps `CASSETTE_LOW`->`CASSETTE_EMPTY`; KAFK `atm_status=Out of Service`, `transaction_rate_tps=0` |
| A3 | JVM memory leak -> OOM | PROM, GCP, TERM | PROM `jvm_memory_used_bytes` rising, `jvm_gc_pause_seconds_sum` spiking; TERM FATAL `OutOfMemoryError` |
| A4 | Container restart loop | GCP, TERM | GCP `restart_count` incrementing; TERM repeated `event_type=STARTUP` with new `container_id` |
| A5 | High response time + success drop | KAFK, ATMA | KAFK `response_time_ms` >> baseline, `transaction_success_rate` drop, `failure_count` spike; ATMA `event_type=TIMEOUT` |
| A6 | OS memory pressure -> app timeout | WINOS, ATMA | WINOS `memory_usage_percent`->~100%, `network_errors` rising; ATMA subsequent `event_type=TIMEOUT` |
| A7 | Malformed / out-of-order Kafka event | KAFK, PROM | KAFK timestamp not monotonic vs offset, or `atm_status=null` / missing fields; PROM non-numeric `metric_value` |

---

## 4. File Naming Convention

| Source | Format | Filename |
|---|---|---|
| ATM Application Log | JSON | `atm_application_log.json` |
| ATM Hardware Sensor Log | JSON | `atm_hardware_sensor_log.json` |
| Terminal Handler App Log | JSON | `terminal_handler_app_log.json` |
| Kafka ATM Metrics Stream | JSON | `kafka_atm_metrics_stream.json` |
| Prometheus Metrics | CSV | `prometheus_metrics.csv` |
| Windows OS Metrics | CSV | `windows_os_metrics.csv` |
| GCP Cloud Metrics | CSV | `gcp_cloud_metrics.csv` |

All synthetic files are written to `data/synthetic/`.
