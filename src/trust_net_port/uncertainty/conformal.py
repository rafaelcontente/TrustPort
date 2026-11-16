
import numpy as np
from sklearn.base import BaseEstimator


class SplitConformalPredictor:
    def __init__(self, base_model: BaseEstimator, alpha: float = 0.10, max_interval_width: float = 10.0):
        self.base_model = base_model
        self.alpha = alpha
        self.max_interval_width = max_interval_width
        self.quantile = 0.0
        self.calibration_residuals: np.ndarray | None = None

    def calibrate(self, X_cal: np.ndarray, y_cal: np.ndarray) -> None:
        if not hasattr(self.base_model, 'coef_'):
            raise RuntimeError('Model must be fit on training data before calibration.')
        y_pred_cal = self.base_model.predict(X_cal)
        self.calibration_residuals = np.abs(y_cal - y_pred_cal)
        n = len(self.calibration_residuals)
        q_level = np.ceil((n + 1) * (1 - self.alpha)) / n
        q_level = min(q_level, 1.0)
        self.quantile = float(np.quantile(self.calibration_residuals, q_level))

    def predict_interval(self, X_test: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        y_pred = self.base_model.predict(X_test)
        lower = y_pred - self.quantile
        upper = y_pred + self.quantile
        return lower, y_pred, upper

    def check_drift(self, X_new: np.ndarray, y_new: np.ndarray, threshold: float = 0.05) -> bool:
        if self.calibration_residuals is None:
            raise RuntimeError('Must calibrate before checking drift.')
        y_pred_new = self.base_model.predict(X_new)
        new_residuals = np.abs(y_new - y_pred_new)
        mean_cal = np.mean(self.calibration_residuals)
        mean_new = np.mean(new_residuals)
        return (mean_new - mean_cal) / (mean_cal + 1e-8) > 0.20

    def is_high_uncertainty(self, lower: np.ndarray, upper: np.ndarray) -> np.ndarray:
        return (upper - lower) > self.max_interval_width
