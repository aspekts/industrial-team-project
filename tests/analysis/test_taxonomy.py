import sqlite3
import pytest

from src.analysis.taxonomy import AnomalyTaxonomy, STATIC_TAXONOMY


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test.db")


@pytest.fixture
def taxonomy(db_path):
    t = AnomalyTaxonomy(db_path=db_path)
    t.seed_static()
    return t


class TestSeedStatic:
    def test_seeds_all_static_entries(self, taxonomy, db_path):
        entries = taxonomy.get_all()
        assert len(entries) == len(STATIC_TAXONOMY)

    def test_all_entries_are_static(self, taxonomy):
        for entry in taxonomy.get_all():
            assert entry["discovery_method"] == "static"

    def test_known_anomaly_types_present(self, taxonomy):
        types = {e["anomaly_type"] for e in taxonomy.get_all()}
        assert {"A1", "A2", "A4", "A5", "A6", "A7"}.issubset(types)

    def test_seed_is_idempotent(self, taxonomy, db_path):
        taxonomy.seed_static()
        taxonomy.seed_static()
        entries = taxonomy.get_all()
        assert len(entries) == len(STATIC_TAXONOMY)

    def test_static_entries_have_required_fields(self, taxonomy):
        for entry in taxonomy.get_all():
            assert entry["anomaly_type"]
            assert entry["anomaly_name"]
            assert entry["severity"] in ("CRITICAL", "WARNING", "INFO")
            assert entry["source"]
            assert entry["discovery_method"] == "static"


class TestRegisterDynamic:
    def test_registers_new_dynamic_entry(self, taxonomy):
        taxonomy.register_dynamic(
            anomaly_type="ML-KAFK",
            anomaly_name="ML anomaly cluster (Kafka metrics)",
            severity="WARNING",
            source="KAFK",
            description="IsolationForest detected outlier rows in KAFK source.",
        )
        dynamic = taxonomy.get_by_method("dynamic")
        assert len(dynamic) == 1
        assert dynamic[0]["anomaly_type"] == "ML-KAFK"
        assert dynamic[0]["discovery_method"] == "dynamic"

    def test_register_does_not_duplicate_on_rerun(self, taxonomy):
        for _ in range(3):
            taxonomy.register_dynamic(
                anomaly_type="ML-WINOS",
                anomaly_name="ML anomaly cluster (Windows OS metrics)",
                severity="WARNING",
                source="WINOS",
            )
        dynamic = taxonomy.get_by_method("dynamic")
        winos = [e for e in dynamic if e["anomaly_type"] == "ML-WINOS"]
        assert len(winos) == 1

    def test_dynamic_and_static_coexist(self, taxonomy):
        taxonomy.register_dynamic(
            anomaly_type="ML-GCP",
            anomaly_name="ML anomaly cluster (GCP cloud metrics)",
            severity="WARNING",
            source="GCP",
        )
        all_entries = taxonomy.get_all()
        methods = {e["discovery_method"] for e in all_entries}
        assert methods == {"static", "dynamic"}

    def test_multiple_dynamic_sources(self, taxonomy):
        for source in ("KAFK", "WINOS", "GCP", "PROM"):
            taxonomy.register_dynamic(
                anomaly_type=f"ML-{source}",
                anomaly_name=f"ML cluster ({source})",
                severity="WARNING",
                source=source,
            )
        dynamic = taxonomy.get_by_method("dynamic")
        assert len(dynamic) == 4


class TestGetAll:
    def test_returns_list_of_dicts(self, taxonomy):
        entries = taxonomy.get_all()
        assert isinstance(entries, list)
        assert all(isinstance(e, dict) for e in entries)

    def test_static_before_dynamic_in_order(self, taxonomy):
        taxonomy.register_dynamic(
            anomaly_type="ML-KAFK",
            anomaly_name="ML cluster",
            severity="WARNING",
            source="KAFK",
        )
        entries = taxonomy.get_all()
        methods = [e["discovery_method"] for e in entries]
        # static entries appear first (ORDER BY discovery_method ASC)
        first_dynamic = next(i for i, m in enumerate(methods) if m == "dynamic")
        assert all(m == "static" for m in methods[:first_dynamic])


class TestRoundTrip:
    def test_persisted_entry_round_trips(self, db_path):
        t = AnomalyTaxonomy(db_path=db_path)
        t.seed_static()
        t.register_dynamic(
            anomaly_type="ML-PROM",
            anomaly_name="ML anomaly cluster (Prometheus metrics)",
            severity="WARNING",
            source="PROM",
            description="Detected via IsolationForest.",
        )

        # Re-open connection to confirm persistence
        t2 = AnomalyTaxonomy(db_path=db_path)
        entries = t2.get_all()
        types = {e["anomaly_type"] for e in entries}
        assert "ML-PROM" in types
        assert "A1" in types

    def test_database_schema_has_correct_columns(self, db_path):
        t = AnomalyTaxonomy(db_path=db_path)
        t.seed_static()
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("PRAGMA table_info(anomaly_taxonomy)")
            columns = {row[1] for row in cursor.fetchall()}
        expected = {
            "anomaly_type", "anomaly_name", "severity", "source",
            "discovery_method", "description", "registered_at",
        }
        assert expected == columns
