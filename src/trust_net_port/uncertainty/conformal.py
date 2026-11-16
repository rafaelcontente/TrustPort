import numpy as np
from sklearn.base import BaseEstimator
from typing import Tuple

class SplitConformalPredictor:
    def __init__(self, base_model: BaseEstimator, alpha: float = 0.10):
        self.base_model = base_model
        self.alpha = alpha
        self.quantile = 0.0

    def calibrate(self, X_cal: np.ndarray, y_cal: np.ndarray) -> None:
        if not hasattr(self.base_model, 'coef_'):
            raise RuntimeError('Model must be fit on training data before calibration.')
        y_pred_cal = self.base_model.predict(X_cal)
        residuals = np.abs(y_cal - y_pred_cal)
        n = len(residuals)
        q_level = np.ceil((n + 1) * (1 - self.alpha)) / n
        q_level = min(q_level, 1.0)
        self.quantile = float(np.quantile(residuals, q_level))

    def predict_interval(self, X_test: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        y_pred = self.base_model.predict(X_test)
        return y_pred - self.quantile, y_pred, y_pred + self.quantile
