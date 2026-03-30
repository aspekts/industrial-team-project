import os
import sqlite3
import pandas as pd

""" 
FeatureExtractor is responsible for querying the sqlite database and building a flat numeric feature matrix ased on the metric rich tables only. 
Features to extract per table:

Table	Fields to use
KAFK	transaction_rate_tps, response_time_ms, transaction_success_rate, failure_count
WINOS	cpu_usage_percent, memory_usage_percent, network_errors, event_log_errors_last_min
GCP	    cpu_usage_percent, memory_usage_bytes, restart_count, network_ingress_bytes
PROM	pivot on metric_name (JVM heap, GC pause, CPU usage) → numeric columns
"""
class FeatureExtractor:
    def __init__(self, db_path):
        self.db_path = db_path
    """
    Connect to the sqlite database and load features from the KAFK table. Returns a pdDataFrame with the extracted features.
    """
    def load_kafk_features(self):
        conn = sqlite3.connect(self.db_path)
        query = "SELECT transaction_rate_tps, response_time_ms, transaction_success_rate, failure_count FROM KAFK"
        df_kafk = pd.read_sql_query(query, conn)
        conn.close()
        return df_kafk
    
    """
    Connect to the sqlite database and load features from the WINOS table. Returns a pdDataFrame with the extracted features.
    """
    def load_winos_features(self):
        conn = sqlite3.connect(self.db_path)
        query = "SELECT cpu_usage_percent, memory_usage_percent, network_errors, event_log_errors_last_min FROM WINOS"
        df_winos = pd.read_sql_query(query, conn)
        conn.close()
        return df_winos
    
    """
    Connect to the sqlite database and load features from the GCP table. Returns a pdDataFrame with the extracted features.
    """
    def load_gcp_features(self):
        conn = sqlite3.connect(self.db_path)
        query = "SELECT cpu_usage_percent, memory_usage_bytes, restart_count, network_ingress_bytes FROM GCP"
        df_gcp = pd.read_sql_query(query, conn)
        conn.close()
        return df_gcp

    """
    Connect to the sqlite database and load features from the PROM table. Returns a pdDataFrame with the extracted features pivoted on metric_name.
    """
    def load_prom_features(self):
        conn = sqlite3.connect(self.db_path)
        query = "SELECT metric_name, metric_value FROM PROM"
        df_prom = pd.read_sql_query(query, conn)
        #requires pivoting the PROM table with an aggregation function to get metric_name as columns and metric_value as values
        df_prom_pivot = df_prom.pivot_table(index=df_prom.index, columns='metric_name', values='metric_value')
        
        conn.close()
        return df_prom_pivot

    """
    Load all features from the KAFK, WINOS, GCP, and PROM tables and merge them into a single pdDataFrame. Returns the merged feature matrix. Dispatches and fills nulls. Record null values for documentation. 
    """
    def get_all_features(self,source: str):
        df_kafk = self.load_kafk_features() if source == 'KAFK' else pd.DataFrame()
        df_winos = self.load_winos_features() if source == 'WINOS' else pd.DataFrame()
        df_gcp = self.load_gcp_features() if source == 'GCP' else pd.DataFrame()
        df_prom = self.load_prom_features() if source == 'PROM' else pd.DataFrame()

        # Merge all features on a common index (assuming there's a timestamp or ID to merge on)
        df_all = pd.concat([df_kafk, df_winos, df_gcp, df_prom], axis=1)

        # Fill null values with 0 and record the count of nulls for documentation
        null_counts = df_all.isnull().sum()
        log_path = f"data/logs/null_counts_{source}.log"
        os.makedirs("data/logs", exist_ok=True)
        with open(log_path, 'w') as f:
            f.write("Null value counts per feature:\n")
            f.write(str(null_counts))

        df_all_filled = df_all.fillna(0)
        
        return df_all_filled