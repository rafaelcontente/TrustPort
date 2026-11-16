import numpy as np
from sklearn.linear_model import LinearRegression

from trust_net_port.uncertainty.conformal import SplitConformalPredictor


def test_conformal_segmented_coverage():
    """Cobertura em segmentos de risco (cauda heterocedástica)."""
    np.random.seed(42)
    n_train, n_cal, n_test = 500, 500, 1000
    X_all = np.random.randn(n_train + n_cal + n_test, 1)
    # Ruído moderadamente heterocedástico
    noise = np.abs(X_all[:, 0]) * 0.2 + 0.1
    y_all = 2 * X_all[:, 0] + np.random.randn(n_train + n_cal + n_test) * noise
    
    X_train, X_cal, X_test = np.split(X_all, [n_train, n_train + n_cal])
    y_train, y_cal, y_test = np.split(y_all, [n_train, n_train + n_cal])
    
    base_model = LinearRegression()
    base_model.fit(X_train, y_train)
    cp = SplitConformalPredictor(base_model=base_model, alpha=0.10)
    cp.calibrate(X_cal, y_cal)
    
    lower, _pred, upper = cp.predict_interval(X_test)
    covered = (y_test >= lower) & (y_test <= upper)
    
    high_risk_mask = X_test[:, 0] > 1.0
    if np.sum(high_risk_mask) > 10:
        high_risk_coverage = np.mean(covered[high_risk_mask])
        # NOTA DE AUDITORIA: Conformal Marginal garante 90% em média, mas degrada-se 
        # em caudas heterocedásticas. 0.70 é um baseline realista para este método.
        # Para garantia condicional estrita, seria necessário Conformal Estratificado (Mondrian).
        assert high_risk_coverage >= 0.70, f"High risk coverage {high_risk_coverage:.3f} < 0.70"

def test_conformal_drift_detection():
    """O sistema deve detetar drift quando a distribuição de resíduos muda significativamente."""
    np.random.seed(42)
    n_train, n_cal = 500, 500
    
    X_train = np.random.randn(n_train, 1)
    y_train = 2 * X_train[:, 0] + np.random.randn(n_train) * 0.5
    
    X_cal = np.random.randn(n_cal, 1)
    y_cal = 2 * X_cal[:, 0] + np.random.randn(n_cal) * 0.5
    
    base_model = LinearRegression()
    base_model.fit(X_train, y_train)
    
    cp = SplitConformalPredictor(base_model=base_model, alpha=0.10)
    cp.calibrate(X_cal, y_cal)
    
    # Dados sem drift (mesma distribuição)
    X_no_drift = np.random.randn(100, 1)
    y_no_drift = 2 * X_no_drift[:, 0] + np.random.randn(100) * 0.5
    assert not cp.check_drift(X_no_drift, y_no_drift), "False positive drift detection"
    
    # Dados com drift (ruído 5x maior)
    X_drift = np.random.randn(100, 1)
    y_drift = 2 * X_drift[:, 0] + np.random.randn(100) * 2.5
    assert cp.check_drift(X_drift, y_drift), "Failed to detect significant drift"

def test_conformal_high_uncertainty_triggers_escalation_logic():
    """Intervalos de predição largos devem ser sinalizados para escalonamento."""
    np.random.seed(42)
    X = np.random.randn(100, 1)
    y = 2 * X[:, 0] + np.random.randn(100) * 0.5
    
    base_model = LinearRegression()
    base_model.fit(X, y)
    
    cp = SplitConformalPredictor(base_model=base_model, alpha=0.10, max_interval_width=1.0)
    cp.quantile = 2.0  # Simula alta incerteza
    
    lower, _pred, upper = cp.predict_interval(X)
    is_high_uncertainty = cp.is_high_uncertainty(lower, upper)
    
    # Como quantile=2.0, width = 4.0, que é > max_interval_width (1.0)
    assert np.all(is_high_uncertainty), "Failed to flag high uncertainty intervals"
