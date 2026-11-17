"""Test bias detection with synthetic data.

Tests that the fairness module correctly:
1. Detects bias when present
2. Passes when data is fair
3. Calculates all metrics correctly
4. Generates reports in human-readable and JSON formats
"""

from trust_net_port.fairness.metrics import (
    calculate_all_fairness_metrics,
    check_fairness_thresholds,
    demographic_parity_difference,
    disparate_impact_ratio,
    equal_opportunity_difference,
)
from trust_net_port.fairness.report import export_fairness_report_json, generate_fairness_report


def test_disparate_impact_no_bias():
    """Test DIR when there is no bias (equal positive rates)."""
    y_true = [1, 1, 1, 1, 0, 0, 0, 0]
    y_pred = [1, 1, 0, 0, 1, 1, 0, 0]  # 50% positive for both groups
    protected = [1, 1, 1, 1, 0, 0, 0, 0]
    
    dir_value = disparate_impact_ratio(y_true, y_pred, protected)
    assert 0.9 <= dir_value <= 1.1, f"DIR should be ~1.0, got {dir_value}"


def test_disparate_impact_with_bias():
    """Test DIR when there is bias against unprivileged group."""
    y_true = [1, 1, 1, 1, 1, 1, 1, 1]
    y_pred = [1, 1, 1, 1, 0, 0, 0, 0]  # 100% positive for privileged, 0% for unprivileged
    protected = [1, 1, 1, 1, 0, 0, 0, 0]
    
    dir_value = disparate_impact_ratio(y_true, y_pred, protected)
    assert dir_value < 0.8, f"DIR should be < 0.8 (bias), got {dir_value}"


def test_equal_opportunity_no_bias():
    """Test EOD when there is no bias (equal TPR)."""
    y_true = [1, 1, 1, 1, 1, 1, 0, 0]
    y_pred = [1, 1, 0, 0, 1, 1, 0, 0]  # 50% TPR for both groups
    protected = [1, 1, 1, 1, 0, 0, 0, 0]
    
    eod_value = equal_opportunity_difference(y_true, y_pred, protected)
    assert abs(eod_value) < 0.1, f"EOD should be ~0, got {eod_value}"


def test_demographic_parity_no_bias():
    """Test DPD when there is no bias (equal positive rates)."""
    y_pred = [1, 1, 0, 0, 1, 1, 0, 0]  # 50% positive for both groups
    protected = [1, 1, 1, 1, 0, 0, 0, 0]
    
    dpd_value = demographic_parity_difference(y_pred, protected)
    assert abs(dpd_value) < 0.1, f"DPD should be ~0, got {dpd_value}"


def test_calculate_all_metrics():
    """Test that all metrics are calculated correctly."""
    y_true = [1, 1, 1, 1, 1, 1, 1, 1]
    y_pred = [1, 1, 1, 1, 0, 0, 0, 0]
    protected = [1, 1, 1, 1, 0, 0, 0, 0]
    
    metrics = calculate_all_fairness_metrics(y_true, y_pred, protected)
    
    assert 'disparate_impact_ratio' in metrics
    assert 'equal_opportunity_difference' in metrics
    assert 'demographic_parity_difference' in metrics
    assert 'statistical_parity_difference' in metrics
    
    # With this data, DIR should be 0 (bias)
    assert metrics['disparate_impact_ratio'] == 0.0


def test_check_fairness_thresholds_pass():
    """Test that fair data passes all thresholds."""
    metrics = {
        'disparate_impact_ratio': 1.0,
        'equal_opportunity_difference': 0.0,
        'demographic_parity_difference': 0.0,
        'statistical_parity_difference': 0.0,
    }
    
    checks = check_fairness_thresholds(metrics)
    
    assert checks['disparate_impact_ratio_pass'] is True
    assert checks['equal_opportunity_difference_pass'] is True
    assert checks['demographic_parity_difference_pass'] is True
    assert checks['statistical_parity_difference_pass'] is True


def test_check_fairness_thresholds_fail():
    """Test that biased data fails thresholds."""
    metrics = {
        'disparate_impact_ratio': 0.5,  # Below 0.8 threshold
        'equal_opportunity_difference': 0.3,  # Above 0.1 threshold
        'demographic_parity_difference': 0.2,  # Above 0.1 threshold
        'statistical_parity_difference': 0.2,
    }
    
    checks = check_fairness_thresholds(metrics)
    
    assert checks['disparate_impact_ratio_pass'] is False
    assert checks['equal_opportunity_difference_pass'] is False
    assert checks['demographic_parity_difference_pass'] is False


def test_generate_fairness_report():
    """Test that fairness report is generated correctly."""
    metrics = {
        'disparate_impact_ratio': 1.0,
        'equal_opportunity_difference': 0.0,
        'demographic_parity_difference': 0.0,
        'statistical_parity_difference': 0.0,
    }
    checks = check_fairness_thresholds(metrics)
    
    report = generate_fairness_report(
        metrics=metrics,
        checks=checks,
        protected_attribute_name="gender",
        privileged_group_name="male",
        unprivileged_group_name="female",
        sample_size=1000
    )
    
    assert "FAIRNESS & BIAS DETECTION REPORT" in report
    assert "NO BIAS DETECTED" in report
    assert "gender" in report
    assert "1000" in report


def test_generate_fairness_report_with_bias():
    """Test that fairness report detects bias correctly."""
    metrics = {
        'disparate_impact_ratio': 0.5,
        'equal_opportunity_difference': 0.3,
        'demographic_parity_difference': 0.2,
        'statistical_parity_difference': 0.2,
    }
    checks = check_fairness_thresholds(metrics)
    
    report = generate_fairness_report(
        metrics=metrics,
        checks=checks,
        protected_attribute_name="race",
        privileged_group_name="group_a",
        unprivileged_group_name="group_b",
        sample_size=500
    )
    
    assert "BIAS DETECTED" in report
    assert "race" in report


def test_export_fairness_report_json():
    """Test that JSON export works correctly."""
    metrics = {
        'disparate_impact_ratio': 1.0,
        'equal_opportunity_difference': 0.0,
        'demographic_parity_difference': 0.0,
        'statistical_parity_difference': 0.0,
    }
    checks = check_fairness_thresholds(metrics)
    
    json_report = export_fairness_report_json(
        metrics=metrics,
        checks=checks,
        protected_attribute_name="age",
        sample_size=2000
    )
    
    import json
    report_dict = json.loads(json_report)
    
    assert report_dict['overall_fair'] is True
    assert report_dict['sample_size'] == 2000
    assert report_dict['protected_attribute'] == "age"
    assert 'metrics' in report_dict
    assert 'threshold_checks' in report_dict
