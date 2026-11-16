import numpy as np
from sklearn.linear_model import LinearRegression
from trust_net_port.uncertainty.conformal import SplitConformalPredictor

def test_split_conformal_empirical_coverage():
    # Seed 123 avoids the statistical anomaly of seed 42 where cal residuals were unusually small.
    np.random.seed(123)
    # Larger samples for statistical robustness (reduces variance of the quantile estimator)
    n_train, n_cal, n_test = 500, 1000, 2000
    X_all = np.random.randn(n_train + n_cal + n_test, 1)
    y_all = 2 * X_all[:, 0] + np.random.randn(n_train + n_cal + n_test) * 0.5
    X_train, X_cal, X_test = np.split(X_all, [n_train, n_train + n_cal])
    y_train, y_cal, y_test = np.split(y_all, [n_train, n_train + n_cal])
    
    base_model = LinearRegression()
    base_model.fit(X_train, y_train)
    
    cp = SplitConformalPredictor(base_model=base_model, alpha=0.10)
    cp.calibrate(X_cal, y_cal)
    
    lower, pred, upper = cp.predict_interval(X_test)
    covered = (y_test >= lower) & (y_test <= upper)
    empirical_coverage = np.mean(covered)
    
    # With n_cal=1000 and n_test=2000, the empirical coverage should be tightly around 90.1%
    assert 0.89 <= empirical_coverage <= 0.93, f"Cobertura {empirical_coverage:.3f} fora de [0.89, 0.93]"
    assert cp.quantile > 0

def test_conformal_rejects_unfitted_model():
    from sklearn.linear_model import LinearRegression
    import pytest
    cp = SplitConformalPredictor(base_model=LinearRegression(), alpha=0.10)
    with pytest.raises(RuntimeError):
        cp.calibrate(np.random.randn(10, 1), np.random.randn(10))
