# main.py
from src.parsers.ingest import run_ingestion
from src.cleaning.schemas import LOG_SCHEMAS
from src.cleaning.data_cleaning import LogCleaner
from src.cleaning.database import DatabaseHandler
from src.dashboard.server import create_app
from src.analysis.detect import Detection
from src.analysis.correlate import Correlator
from src.ml.scorer import AnomalyScorer

from configparser import ConfigParser
import time

config = ConfigParser()
config.read("config.ini")

def run_pipeline():
    # Stage 1: Ingest raw log files into a structured format
    run_ingestion()

    # Stage 2: Clean the ingested data and store it in a SQLite database
    RAW_DATA_DIR = config.get("PATHS", "raw_data_dir")
    CLEANED_DB_PATH = config.get("PATHS", "cleaned_db_path")
    ERROR_PATH = config.get("PATHS", "error_path")

    db_handler = DatabaseHandler(db_path=CLEANED_DB_PATH)
    db_handler.setup_database(LOG_SCHEMAS)

    cleaner = LogCleaner(db_handler=db_handler, input_dir=RAW_DATA_DIR)
    cleaner.process_all_files()

    # Stage 3: Run rules-based anomaly detection and store grouped results
    Detection(db_path=CLEANED_DB_PATH).store_detections()

    # Stage 4: Score anomalies with Isolation Forest and write results back to the database
    scorer = AnomalyScorer(db_path=CLEANED_DB_PATH)
    scorer.score_and_store_anomalies()

    # Stage 5: Correlate detections into cross-source incidents
    Correlator(db_path=CLEANED_DB_PATH).store_incidents()

if __name__ == "__main__":
    run_pipeline()
    app = create_app()
    host = config.get("NETWORK", "host")
    port = config.getint("NETWORK", "port")
    print(f"[INFO] Pipeline complete. Starting dashboard on http://{host}:{port}")
    app.run(host, port=port, debug=False)
