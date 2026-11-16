import numpy as np
from sklearn.base import BaseEstimator

class ConformalRegressor:
    """
    Split Conformal Prediction wrapper.
    Calculates a valid prediction interval with statistical guarantees (1 - alpha).
    """
    def __init__(self, base_model: BaseEstimator, alpha: float = 0.10):
        self.base_model = base_model
        self.alpha = alpha
        self.quantile = 0.0

    def calibrate(self, X_cal: np.ndarray, y_cal: np.ndarray) -> 'ConformalRegressor':
        """Calibrates the conformal predictor using a hold-out calibration set."""
        predictions = self.base_model.predict(X_cal)
        residuals = np.abs(y_cal - predictions)
        # Use 'higher' to be conservative (guarantees >= 1-alpha coverage)
        self.quantile = float(np.quantile(residuals, 1 - self.alpha, method='higher'))
        return self

    def predict_interval(self, X: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Returns (lower_bound, prediction, upper_bound)."""
        predictions = self.base_model.predict(X)
        lower_bound = predictions - self.quantile
        upper_bound = predictions + self.quantile
        return lower_bound, predictions, upper_bound
