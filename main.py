# main.py
from src.parsers.ingest import run_ingestion
from src.cleaning.schemas import LOG_SCHEMAS
from src.cleaning.data_cleaning import LogCleaner
from src.cleaning.database import DatabaseHandler
from src.ml.scorer import AnomalyScorer

def run_pipeline():
    # Stage 1: Ingest raw log files into a structured format (e.g., CSV or directly into a database)
    run_ingestion() 
    # Stage 2: Clean the ingested data and store it in a SQLite database for easy access by the ML components
    RAW_DATA_DIR = "data/raw"
    CLEANED_DB_PATH = "data/clean/atm_logs.db"

    db_handler = DatabaseHandler(db_path=CLEANED_DB_PATH)
    
    db_handler.setup_database(LOG_SCHEMAS)
    cleaner = LogCleaner(db_handler=db_handler, input_dir=RAW_DATA_DIR)

    cleaner.process_all_files()

    #Stage 4: Score anomalies and write results back to the database
    scorer = AnomalyScorer(db_path=CLEANED_DB_PATH)
    scorer.score_and_store_anomalies()
if __name__ == "__main__":
    run_pipeline()