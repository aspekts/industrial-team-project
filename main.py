# main.py
import os
from src.parsers.ingest import run_ingestion
from src.cleaning.schemas import LOG_SCHEMAS
from src.cleaning.data_cleaning import LogCleaner
from src.cleaning.database import DatabaseHandler
from src.dashboard.server import create_app
from src.analysis.detect import Detection
from src.ml.scorer import AnomalyScorer

def run_pipeline():
    # Stage 1: Ingest raw log files into a structured format
    run_ingestion()

    # Stage 2: Clean the ingested data and store it in a SQLite database
    RAW_DATA_DIR = "data/raw"
    CLEANED_DB_PATH = "data/clean/atm_logs.db"

    db_handler = DatabaseHandler(db_path=CLEANED_DB_PATH)
    db_handler.setup_database(LOG_SCHEMAS)

    cleaner = LogCleaner(db_handler=db_handler, input_dir=RAW_DATA_DIR)
    cleaner.process_all_files()

    # Stage 3: Run rules-based anomaly detection and store grouped results
    Detection(db_path=CLEANED_DB_PATH).store_detections()

    # Stage 4: Score anomalies with Isolation Forest and write results back to the database
    scorer = AnomalyScorer(db_path=CLEANED_DB_PATH)
    scorer.score_and_store_anomalies()

if __name__ == "__main__":
<<<<<<< Updated upstream
    run_pipeline()
=======
    run_pipeline()
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    print(f"[INFO] Pipeline complete. Starting dashboard on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)

 
>>>>>>> Stashed changes
