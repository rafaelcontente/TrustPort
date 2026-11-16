import pytest
import numpy as np
from sklearn.dummy import DummyRegressor
from trust_net_port.uncertainty.conformal import ConformalRegressor

def test_conformal_calibration_and_interval():
    # Create dummy data
    X_cal = np.array([[1], [2], [3], [4], [5]])
    y_cal = np.array([10, 20, 30, 40, 50])
    
    model = DummyRegressor(strategy='mean')
    model.fit(X_cal, y_cal) # Predicts 30 for everything
    
    cp = ConformalRegressor(base_model=model, alpha=0.20) # 80% coverage
    cp.calibrate(X_cal, y_cal)
    
    # Residuals are: |10-30|=20, |20-30|=10, |30-30|=0, |40-30|=10, |50-30|=20
    # Quantile 0.80 of [0, 10, 10, 20, 20] is 20.0
    assert cp.quantile == 20.0
    
    # Test prediction interval
    X_test = np.array([[6]])
    lower, pred, upper = cp.predict_interval(X_test)
    
    assert pred[0] == 30.0
    assert lower[0] == 10.0
    assert upper[0] == 50.0
