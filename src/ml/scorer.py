import sqlite3
from datetime import date

import pandas as pd

from .features import FeatureExtractor
from .model import AnomalyDetector

SOURCES = ("KAFK", "WINOS", "GCP", "PROM")

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
        conn = sqlite3.connect(self.db_path)

        for source in SOURCES:
            # Load and train a fresh detector per source (feature shapes differ)
            features = self.feature_extractor.get_all_features(source)
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

            results_df.to_sql('ml_anomaly_scores', conn, if_exists='append', index=False)

        conn.close()