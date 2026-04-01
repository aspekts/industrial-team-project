import sqlite3
from datetime import date

import pandas as pd

from .features import FeatureExtractor
from .model import AnomalyDetector
from src.analysis.taxonomy import AnomalyTaxonomy

SOURCES = ("KAFK", "WINOS", "GCP", "PROM")

_SOURCE_LABELS = {
    "KAFK": "Kafka ATM metrics",
    "WINOS": "Windows OS metrics",
    "GCP": "GCP cloud metrics",
    "PROM": "Prometheus metrics",
}

"""
The AnomalyScorer class is responsible for orchestrating the feature extraction and anomaly detection processes. It uses the FeatureExtractor to load features from the database and the AnomalyDetector to identify anomalies based on those features. The class provides methods to score new data and update the model with new data over time. This class would also append anomaly scores to the original feature matrix for further analysis and documentation. These scores are then written back to the database for record-keeping and future reference.

Output schema for ml_anomaly_scores:

Column	Type	Notes
source	TEXT	KAFK, WINOS, GCP, PROM
row_index	INTEGER	Row index from source table (join key)
timestamp	TEXT	From source record
atm_id	TEXT	Nullable (PROM has no atm_id)
anomaly_score	REAL	Raw IF score; lower = more anomalous
is_anomaly	INTEGER	1 = anomaly, 0 = normal
model_version	TEXT	Datestamp or hash, e.g. 2026-03-24
"""
class AnomalyScorer:
    def __init__(self, db_path):
        self.db_path = db_path
        self.feature_extractor = FeatureExtractor(db_path)
        self.anomaly_detector = AnomalyDetector()

    """
    Load features from the database, score them using the anomaly detector, and write the results back to the database. This method orchestrates the entire process of feature extraction, anomaly detection, and result storage.
    """
    def score_and_store_anomalies(self):
        model_version = date.today().isoformat()
        taxonomy = AnomalyTaxonomy(db_path=self.db_path)

        for source in SOURCES:
            # Load and train a fresh detector per source (feature shapes differ)
            features = self.feature_extractor.get_all_features(source)
            if features.empty:
                print(f"[INFO] {source}: no features available, skipping.")
                continue
            detector = AnomalyDetector()
            detector.train(features)

            anomaly_scores = detector.score(features)
            is_anomaly = (anomaly_scores < 0).astype(int)

            results_df = pd.DataFrame({
                'source': source,
                'row_index': features.index,
                'timestamp': None,   # populated from source record when available
                'atm_id': None,      # nullable — PROM has no atm_id
                'anomaly_score': anomaly_scores,
                'is_anomaly': is_anomaly,
                'model_version': model_version,
            })

            with sqlite3.connect(self.db_path) as conn:
                results_df.to_sql('ml_anomaly_scores', conn, if_exists='append', index=False)

            anomaly_count = int(is_anomaly.sum())
            print(f"[INFO] {source}: scored {len(results_df)} rows, {anomaly_count} anomalies.")

            if anomaly_count > 0:
                label = _SOURCE_LABELS.get(source, source)
                taxonomy.register_dynamic(
                    anomaly_type=f"ML-{source}",
                    anomaly_name=f"ML-detected anomaly cluster ({label})",
                    severity="WARNING",
                    source=source,
                    description=(
                        f"Isolation Forest identified {anomaly_count} anomalous rows "
                        f"in {label} (model version {model_version}). "
                        f"Patterns fall outside the normal feature distribution for this source."
                    ),
                )

        print("[INFO] Storing and scoring anomalies complete.")
