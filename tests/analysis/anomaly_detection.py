# Assuming data is imported and cleaned into the atm_logs.db sqlite database.

from analysis.analyse_data import AnalysisData

def test_check_network_errors():
    analysis = AnalysisData(db_path="data/clean/atm_logs.db")
    results = analysis.check_network_errors()
    
    assert isinstance(results, list), "Expected results to be a list"
    for record in results:
        assert 'source' in record, "Missing 'source' field in result record"
        assert record['source'] in ['ATMA', 'KAFK', 'TERM'], f"Unexpected source: {record['source']}"


def test_check_cash_cassette_depletion():
    analysis = AnalysisData(db_path="data/clean/atm_logs.db")
    findings = analysis.check_cash_cassette_depletion()

    assert isinstance(findings, list), "Expected findings to be a list"
    for record in findings:
        assert 'source' in record, "Missing 'source' field in cassette finding record"
        assert record['source'] in ['ATMH', 'KAFK'], f"Unexpected source: {record['source']}"


def test_check_memory_leaks():
    analysis = AnalysisData(db_path="data/clean/atm_logs.db")
    findings = analysis.check_memory_leaks()

    assert isinstance(findings, list), "Expected findings to be a list"
    for record in findings:
        assert 'source' in record, "Missing 'source' field in memory leak finding record"
        assert record['source'] in ['PROM', 'GCP', 'TERM'], f"Unexpected source: {record['source']}"


def test_check_container_restarts():
    analysis = AnalysisData(db_path="data/clean/atm_logs.db")
    findings = analysis.check_container_restarts()

    assert isinstance(findings, list), "Expected findings to be a list"
    for record in findings:
        assert 'source' in record, "Missing 'source' field in container restart finding record"
        assert record['source'] in ['GCP', 'TERM'], f"Unexpected source: {record['source']}"


def test_check_performance_degradation():
    analysis = AnalysisData(db_path="data/clean/atm_logs.db")
    findings = analysis.check_performance_degradation()

    assert isinstance(findings, list), "Expected findings to be a list"
    for record in findings:
        assert 'source' in record, "Missing 'source' field in performance degradation finding record"
        assert record['source'] in ['KAFK'], f"Unexpected source: {record['source']}"


def test_check_windows_os_metrics():
    analysis = AnalysisData(db_path="data/clean/atm_logs.db")
    findings = analysis.check_windows_os_metrics()

    assert isinstance(findings, list), "Expected findings to be a list"
    for record in findings:
        assert 'source' in record, "Missing 'source' field in Windows OS metrics finding record"
        assert record['source'] in ['WINOS'], f"Unexpected source: {record['source']}"


def test_check_kafka_events():
    analysis = AnalysisData(db_path="data/clean/atm_logs.db")
    findings = analysis.check_kafka_events()

    assert isinstance(findings, list), "Expected findings to be a list"
    for record in findings:
        assert 'source' in record, "Missing 'source' field in Kafka events finding record"
        assert record['source'] in ['KAFK'], f"Unexpected source: {record['source']}"

