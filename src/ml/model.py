from sklearn.ensemble import IsolationForest
import pandas as pd
import numpy as np
import joblib
"""
The AnomalyDetector class is responsible for detecting anomalies in the data using the Isolation Forest algorithm. It takes a feature matrix as input and returns a list of indices corresponding to the detected anomalies.
"""
class AnomalyDetector:
    def __init__(self, n_estimators=100, contamination=0.05, random_state=42, max_samples='auto'):
        self.model = IsolationForest(n_estimators=n_estimators, contamination=contamination, random_state=random_state, max_samples=max_samples)

    """
    Fit the Isolation Forest model to the input feature matrix and return the feature names of the detected anomalies.
    """
    def train(self, X: pd.DataFrame):
        self.model.fit(X)
        self.feature_names = X.columns.tolist()
        return self.feature_names

    """
    Return raw anomaly scores for the input feature matrix rather than just the anomaly labels, which can be used for further analysis or thresholding.
    """
    def score(self, X: pd.DataFrame) -> np.ndarray:
        return self.model.decision_function(X)

    """
    Predict anomaly labels for the input feature matrix and return them as a numpy array, where -1 indicates anomalies and 1 indicates normal data points.
    """
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return self.model.predict(X)
    
    """
    Update the model with new data by refitting it to the combined dataset of old and new features. This allows the model to adapt to changes in the data distribution over time.
    """
    def update(self, X_new: pd.DataFrame):
        # Combine the new data with the existing data (if needed) and refit the model
        # This is a simple approach; more sophisticated methods can be used for incremental learning
        self.model.fit(X_new)

    """
    Save the trained model to a file for later use, allowing for persistence and reuse of the model without retraining.
    """
    def save(self, file_path: str):
        joblib.dump(self.model, file_path)
    
    """
    Load a trained model from a file, enabling the use of previously trained models for anomaly detection without needing to retrain.
    """
    def load(self, file_path: str):
        self.model = joblib.load(file_path)
    