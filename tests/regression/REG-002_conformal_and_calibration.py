import pytest
import numpy as np
from sklearn.calibration import calibration_curve

def test_conformal_coverage_bounds():
    target_coverage = 0.90
    empirical_coverage = 0.915
    assert abs(empirical_coverage - target_coverage) <= 0.02, "Coverage must be within +/- 2% of target."

def test_expected_calibration_error():
    y_true = np.array([1, 1, 1, 1, 1, 0, 0, 0, 0, 0])
    y_prob = np.array([1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=3)
    ece = np.mean(np.abs(prob_true - prob_pred))
    assert ece < 0.05, f"ECE {ece} must be less than 0.05."
