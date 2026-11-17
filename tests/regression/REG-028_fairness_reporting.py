"""Tests for fairness reporting functions."""

import json

from trust_net_port.fairness.metrics import (
    check_fairness_thresholds,
    export_fairness_report_json,
    generate_fairness_report,
)


def test_generate_fairness_report_pass():
    """Test that a passing fairness report is generated correctly."""
    metrics = {
        "disparate_impact_ratio": 0.95,
        "equal_opportunity_difference": 0.05,
        "demographic_parity_difference": 0.05,
        "statistical_parity_difference": 0.05,
    }
    checks = check_fairness_thresholds(metrics)

    report = generate_fairness_report(
        metrics=metrics,
        checks=checks,
        protected_attribute_name="gender",
        privileged_group_name="male",
        unprivileged_group_name="female",
        sample_size=1000,
    )

    assert "FAIRNESS & BIAS DETECTION REPORT" in report
    assert "gender" in report
    assert "Sample Size: 1000" in report
    assert "NO BIAS DETECTED" in report
    assert "0.9500" in report  # Check formatting


def test_generate_fairness_report_fail():
    """Test that a failing fairness report highlights bias."""
    metrics = {
        "disparate_impact_ratio": 0.60,  # Below 0.8 threshold
        "equal_opportunity_difference": 0.15,
        "demographic_parity_difference": 0.15,
        "statistical_parity_difference": 0.15,
    }
    checks = check_fairness_thresholds(metrics)

    report = generate_fairness_report(
        metrics=metrics,
        checks=checks,
        protected_attribute_name="age",
        sample_size=500,
    )

    assert "BIAS DETECTED" in report
    assert "potential bias against the unprivileged group" in report


def test_export_fairness_report_json():
    """Test that fairness report exports to valid JSON."""
    metrics = {
        "disparate_impact_ratio": 1.0,
        "equal_opportunity_difference": 0.0,
        "demographic_parity_difference": 0.0,
        "statistical_parity_difference": 0.0,
    }
    checks = check_fairness_thresholds(metrics)

    json_str = export_fairness_report_json(
        metrics=metrics,
        checks=checks,
        protected_attribute_name="ethnicity",
        sample_size=2000,
    )

    # Verify it's valid JSON
    report_dict = json.loads(json_str)

    assert report_dict["overall_fair"] is True
    assert report_dict["sample_size"] == 2000
    assert report_dict["protected_attribute"] == "ethnicity"
    assert "metrics" in report_dict
    assert "threshold_checks" in report_dict
