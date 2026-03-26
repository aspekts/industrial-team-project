# Anomaly Detection Reference

This document describes the anomaly detection patterns implemented in the Industrial Team Project, including synthetic anomaly labels, analysis queries, and test expectations.

## 1. Objective

Support end-to-end detection of ATM operational anomalies and synthetic data ground-truth. Key outcomes:
- Label and evaluate anomalies in generated dataset records using `_anomaly` tags.
- Detect real anomaly candidates in cleaned analytics database (`data/clean/atm_logs.db`).
- Provide high-signal alerts spanning ATM app logs, hardware sensor reports, Kafka metrics, Prometheus/GCP metrics, terminal handler logs, and Windows OS metrics.

## 2. Data sources

- `ATMA` - ATM application event log
- `ATMH` - ATM hardware sensor log
- `KAFK` - Kafka-streamed ATM metric snapshots
- `PROM` - Prometheus time-series metrics
- `GCP` - GCP container metrics
- `TERM` - Terminal handler application logs
- `WINOS` - Windows OS telemetry

## 3. Synthetic anomaly labels (generator ground truth)

Synthetic data includes explicit anomaly tags in `_anomaly` field (or `None` for normal). The canonical simulated anomalies:

- `A1`: ATM offline / network disconnect / host unavailable (ATMA/KAFK/TERM)
- `A2`: Cash cassette depletion (ATMH/KAFK)
- `A3`: Memory leak / GC pressure / DB query slowdown (PROM/GCP/TERM)
- `A4`: Container restart loop / OOM + startup churn (GCP/TERM)
- `A5`: High response time + timeout (KAFK/ATMA)
- `A6`: OS memory pressure leading to timeout/slowdown (GCP/TERM/WINOS)
- `A7_OUT_OF_ORDER`: Kafka offset timestamp disorder (KAFK)
- `A7_MALFORMED`: Missing or malformed Kafka fields, Prometheus/synthetic row corruption (KAFK/PROM)

## 4. Analysis checks in `src/analysis/analyse_data.py`

`AnalyseData` methods implement SQL-based detection and are verified by tests in `tests/analysis/anomaly_detection.py`.

### 4.1 `check_network_errors()`
- ATMA: `NETWORK_DISCONNECT` + `ERR-0040`
- ATMA: `TIMEOUT` with `response_time_ms` equal to configured timeout
- KAFK: `atm_status = 'Offline'` and `transaction_failure_reason = 'HOST_UNAVAILABLE'`
- TERM: `event_type = 'NETWORK_TIMEOUT'` for `ATM-GB-0003`

### 4.2 `check_cash_cassette_depletion()`
- ATMH: `CASH_DISPENSER` with `CASSETTE_LOW` | `CASSETTE_EMPTY` and severity thresholds
- KAFK: `Out of Service` + `CASH_DISPENSE_ERROR` or `transaction_rate_tps == 0.0` + `transaction_success_rate == 0.0`

### 4.3 `check_memory_leaks()`
- PROM: `jvm_memory_used_bytes`, `jvm_gc_pause_seconds_sum`, `process_cpu_usage` exceed configured thresholds
- GCP: `cpu_usage_percent` > configured CPU threshold
- TERM: `log_level = FATAL` and `exception_class = OutOfMemoryError`

### 4.4 `check_container_restarts()`
- GCP: `restart_count > 0`
- TERM: `event_type = STARTUP` or `FATAL` `OutOfMemoryError`

### 4.5 `check_performance_degradation()`
- KAFK: `response_time_ms` within configured regression thresholds
- KAFK: `transaction_success_rate` drops to configured thresholds
- KAFK: `failure_count` spikes to configured thresholds

### 4.6 `check_windows_os_metrics()`
- WINOS: `memory_usage_percent` > threshold, `network_errors` > threshold, `cpu_usage_percent` > threshold

### 4.7 `check_kafka_events()`
- KAFK offset order check (e.g., offset 4050 timestamp out of latency order)
- KAFK content quality check (offset 4051 with null `atm_status` or `transaction_rate_tps`)

## 5. Running the checks and tests

1. Generate or load clean dataset:
   - data ingestion via `src/parsers/ingest.py`
   - synthetic generation via `src/synthetic/ncr_generator.py`
2. Build/clean database from parsed data into `data/clean/atm_logs.db`
3. Run tests:
   - `pytest tests/analysis/anomaly_detection.py`
4. Optional ad-hoc analysis:
   - `python -c "from analysis.analyse_data import AnalyseData; print(AnalyseData().check_network_errors())"`

## 6. Extending anomalies

- Add configuration values in `src/analysis/config.ini` for thresholds
- Add new rules to `AnalyseData` methods for new signatures
- Add corresponding coverage tests in `tests/analysis/anomaly_detection.py`

## 7. Notes

- The dataset includes an `_anomaly` field for validation: `None` means normal, non-null means injected scenario.
- Ensure any new anomaly rule stays simple, traceable, and mirror synthetic injection logic for explainability.# Anomaly Detection Reference

This document describes the anomaly detection patterns implemented in the Industrial Team Project, including synthetic anomaly labels, analysis queries, and test expectations.

## 1. Objective

Support end-to-end detection of ATM operational anomalies and synthetic data ground-truth. Key outcomes:
- Label and evaluate anomalies in generated dataset records using `_anomaly` tags.
- Detect real anomaly candidates in cleaned analytics database (`data/clean/atm_logs.db`).
- Provide high-signal alerts spanning ATM app logs, hardware sensor reports, Kafka metrics, Prometheus/GCP metrics, terminal handler logs, and Windows OS metrics.

## 2. Data sources

- `ATMA` - ATM application event log
- `ATMH` - ATM hardware sensor log
- `KAFK` - Kafka-streamed ATM metric snapshots
- `PROM` - Prometheus time-series metrics
- `GCP` - GCP container metrics
- `TERM` - Terminal handler application logs
- `WINOS` - Windows OS telemetry

## 3. Synthetic anomaly labels (generator ground truth)

Synthetic data includes explicit anomaly tags in `_anomaly` field (or `None` for normal). The canonical simulated anomalies:

- `A1`: ATM offline / network disconnect / host unavailable (ATMA/KAFK/TERM)
- `A2`: Cash cassette depletion (ATMH/KAFK)
- `A3`: Memory leak / GC pressure / DB query slowdown (PROM/GCP/TERM)
- `A4`: Container restart loop / OOM + startup churn (GCP/TERM)
- `A5`: High response time + timeout (KAFK/ATMA)
- `A6`: OS memory pressure leading to timeout/slowdown (GCP/TERM/WINOS)
- `A7_OUT_OF_ORDER`: Kafka offset timestamp disorder (KAFK)
- `A7_MALFORMED`: Missing or malformed Kafka fields, Prometheus/synthetic row corruption (KAFK/PROM)

## 4. Analysis checks in `src/analysis/analyse_data.py`

`AnalyseData` methods implement SQL-based detection and are verified by tests in `tests/analysis/anomaly_detection.py`.

### 4.1 `check_network_errors()`
- ATMA: `NETWORK_DISCONNECT` + `ERR-0040`
- ATMA: `TIMEOUT` with `response_time_ms` equal to configured timeout
- KAFK: `atm_status = 'Offline'` and `transaction_failure_reason = 'HOST_UNAVAILABLE'`
- TERM: `event_type = 'NETWORK_TIMEOUT'` for `ATM-GB-0003`

### 4.2 `check_cash_cassette_depletion()`
- ATMH: `CASH_DISPENSER` with `CASSETTE_LOW` | `CASSETTE_EMPTY` and severity thresholds
- KAFK: `Out of Service` + `CASH_DISPENSE_ERROR` or `transaction_rate_tps == 0.0` + `transaction_success_rate == 0.0`

### 4.3 `check_memory_leaks()`
- PROM: `jvm_memory_used_bytes`, `jvm_gc_pause_seconds_sum`, `process_cpu_usage` exceed configured thresholds
- GCP: `cpu_usage_percent` > configured CPU threshold
- TERM: `log_level = FATAL` and `exception_class = OutOfMemoryError`

### 4.4 `check_container_restarts()`
- GCP: `restart_count > 0`
- TERM: `event_type = STARTUP` or `FATAL` `OutOfMemoryError`

### 4.5 `check_performance_degradation()`
- KAFK: `response_time_ms` within configured regression thresholds
- KAFK: `transaction_success_rate` drops to configured thresholds
- KAFK: `failure_count` spikes to configured thresholds

### 4.6 `check_windows_os_metrics()`
- WINOS: `memory_usage_percent` > threshold, `network_errors` > threshold, `cpu_usage_percent` > threshold

### 4.7 `check_kafka_events()`
- KAFK offset order check (e.g., offset 4050 timestamp out of latency order)
- KAFK content quality check (offset 4051 with null `atm_status` or `transaction_rate_tps`)

## 5. Running the checks and tests

1. Generate or load clean dataset:
   - data ingestion via `src/parsers/ingest.py`
   - synthetic generation via `src/synthetic/ncr_generator.py`
2. Build/clean database from parsed data into `data/clean/atm_logs.db`
3. Run tests:
   - `pytest tests/analysis/anomaly_detection.py`
4. Optional ad-hoc analysis:
   - `python -c "from analysis.analyse_data import AnalyseData; print(AnalyseData().check_network_errors())"`

## 6. Extending anomalies

- Add configuration values in `src/analysis/config.ini` for thresholds
- Add new rules to `AnalyseData` methods for new signatures
- Add corresponding coverage tests in `tests/analysis/anomaly_detection.py`

## 7. Notes

- The dataset includes an `_anomaly` field for validation: `None` means normal, non-null means injected scenario.
- Ensure any new anomaly rule stays simple, traceable, and mirror synthetic injection logic for explainability.

## 8. Limitations and assumptions

### 8.1 Assumptions
- The files assumes that `atm_logs.db` file is populated with clean data and that the `config.ini` file is setup with data already.

### 8.2 Limitations
- The file is currently not able to detect anomalies that are not specified already in the file.