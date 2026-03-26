# Assuming data is imported and cleaned into the atm_logs.db sqlite database.

from src.analysis.analyse_data import AnalyseData

def test_check_network_errors():
    analysis = AnalyseData(db_path="data/clean/atm_logs.db")
    results = analysis.check_network_errors()
    
    assert isinstance(results, list), "Expected results to be a list"
    for record in results:
        assert 'source' in record, "Missing 'source' field in result record"
        assert record['source'] in ['ATMA', 'KAFK', 'TERM'], f"Unexpected source: {record['source']}"
        if record['source'] == 'ATMA':
            assert (record['event_type'] == 'NETWORK_DISCONNECT' and record['error_code'] == 'ERR-0040') or (record['event_type'] == 'TIMEOUT' and record['response_time_ms'] == 30000)
        elif record['source'] == 'KAFK':
            assert record['atm_status'] == 'Offline' and record['transaction_failure_reason'] == 'HOST_UNAVAILABLE'
        elif record['source'] == 'TERM':
            assert record['event_type'] == 'NETWORK_TIMEOUT' and record['atm_id'] == 'ATM-GB-0003'


def test_check_cash_cassette_depletion():
    analysis = AnalyseData(db_path="data/clean/atm_logs.db")
    findings = analysis.check_cash_cassette_depletion()

    assert isinstance(findings, list), "Expected findings to be a list"
    for record in findings:
        assert 'source' in record, "Missing 'source' field in cassette finding record"
        assert record['source'] in ['ATMH', 'KAFK'], f"Unexpected source: {record['source']}"
        if record['source'] == 'ATMH':
            assert record['component'] == 'CASH_DISPENSER'
            assert (record['event_type'] == 'CASSETTE_LOW' and record['severity'] == 'WARNING') or (record['event_type'] == 'CASSETTE_EMPTY' and record['severity'] == 'CRITICAL')
        elif record['source'] == 'KAFK':
            assert (record['atm_status'] == 'Out of Service' and record['transaction_failure_reason'] == 'CASH_DISPENSE_ERROR') or (record['transaction_rate_tps'] == 0.0 and record['transaction_success_rate'] == 0.0)


def test_check_memory_leaks():
    analysis = AnalyseData(db_path="data/clean/atm_logs.db")
    findings = analysis.check_memory_leaks()

    assert isinstance(findings, list), "Expected findings to be a list"
    for record in findings:
        assert 'source' in record, "Missing 'source' field in memory leak finding record"
        assert record['source'] in ['PROM', 'GCP', 'TERM'], f"Unexpected source: {record['source']}"
        if record['source'] == 'PROM':
            assert (record['metric_name'] == 'jvm_memory_used_bytes' and record['metric_value'] > 1000000000) or \
                   (record['metric_name'] == 'jvm_gc_pause_seconds_sum' and record['metric_value'] > 10) or \
                   (record['metric_name'] == 'process_cpu_usage' and record['metric_value'] > 0.9)
        elif record['source'] == 'GCP':
            assert record['cpu_usage_percent'] > 90
        elif record['source'] == 'TERM':
            assert record['log_level'] == 'FATAL' and record['exception_class'] == 'OutOfMemoryError'


def test_check_container_restarts():
    analysis = AnalyseData(db_path="data/clean/atm_logs.db")
    findings = analysis.check_container_restarts()

    assert isinstance(findings, list), "Expected findings to be a list"
    for record in findings:
        assert 'source' in record, "Missing 'source' field in container restart finding record"
        assert record['source'] in ['GCP', 'TERM'], f"Unexpected source: {record['source']}"
        if record['source'] == 'GCP':
            assert record['restart_count'] > 0
        elif record['source'] == 'TERM':
            assert record['event_type'] == 'STARTUP' or (record['log_level'] == 'FATAL' and record['exception_class'] == 'OutOfMemoryError')


def test_check_performance_degradation():
    analysis = AnalyseData(db_path="data/clean/atm_logs.db")
    findings = analysis.check_performance_degradation()

    assert isinstance(findings, list), "Expected findings to be a list"
    for record in findings:
        assert 'source' in record, "Missing 'source' field in performance degradation finding record"
        assert record['source'] in ['KAFK'], f"Unexpected source: {record['source']}"
        assert record['response_time_ms'] in [3200, 30000] or record['transaction_success_rate'] in [0.72, 0.5] or record['failure_count'] in [8, 14]


def test_check_windows_os_metrics():
    analysis = AnalyseData(db_path="data/clean/atm_logs.db")
    findings = analysis.check_windows_os_metrics()

    assert isinstance(findings, list), "Expected findings to be a list"
    for record in findings:
        assert 'source' in record, "Missing 'source' field in Windows OS metrics finding record"
        assert record['source'] in ['WINOS'], f"Unexpected source: {record['source']}"
        assert record['memory_usage_percent'] > 0.9 or record['network_errors'] > 20 or record['cpu_usage_percent'] > 90


def test_check_kafka_events():
    analysis = AnalyseData(db_path="data/clean/atm_logs.db")
    findings = analysis.check_kafka_events()

    assert isinstance(findings, list), "Expected findings to be a list"
    for record in findings:
        assert 'source' in record, "Missing 'source' field in Kafka events finding record"
        assert record['source'] in ['KAFK'], f"Unexpected source: {record['source']}"