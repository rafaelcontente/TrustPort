"""Fairness metrics for bias detection."""

from collections.abc import Sequence
import numpy as np


def disparate_impact_ratio(
    y_true: Sequence[int],
    y_pred: Sequence[int],
    protected_attribute: Sequence[int],
    privileged_group: int = 1,
    unprivileged_group: int = 0
) -> float:
    """Calculate disparate impact ratio (DIR)."""
    y_pred_arr = np.array(y_pred)
    protected = np.array(protected_attribute)
    
    privileged_mask = protected == privileged_group
    if privileged_mask.sum() == 0:
        return float('nan')
    
    privileged_positive_rate = y_pred_arr[privileged_mask].mean()
    if privileged_positive_rate == 0:
        return float('inf')
    
    unprivileged_mask = protected == unprivileged_group
    if unprivileged_mask.sum() == 0:
        return float('nan')
    
    unprivileged_positive_rate = y_pred_arr[unprivileged_mask].mean()
    
    return unprivileged_positive_rate / privileged_positive_rate


def equal_opportunity_difference(
    y_true: Sequence[int],
    y_pred: Sequence[int],
    protected_attribute: Sequence[int],
    privileged_group: int = 1,
    unprivileged_group: int = 0
) -> float:
    """Calculate equal opportunity difference (EOD).
    
    EOD = TPR(unprivileged) - TPR(privileged)
    TPR = TP / (TP + FN)
    """
    y_true_arr = np.array(y_true)
    y_pred_arr = np.array(y_pred)
    protected = np.array(protected_attribute)
    
    # TPR for privileged group
    privileged_positives = (protected == privileged_group) & (y_true_arr == 1)
    if privileged_positives.sum() == 0:
        tpr_privileged = 0.0
    else:
        tpr_privileged = y_pred_arr[privileged_positives].mean()
    
    # TPR for unprivileged group
    unprivileged_positives = (protected == unprivileged_group) & (y_true_arr == 1)
    if unprivileged_positives.sum() == 0:
        tpr_unprivileged = 0.0
    else:
        tpr_unprivileged = y_pred_arr[unprivileged_positives].mean()
    
    return tpr_unprivileged - tpr_privileged


def demographic_parity_difference(
    y_pred: Sequence[int],
    protected_attribute: Sequence[int],
    privileged_group: int = 1,
    unprivileged_group: int = 0
) -> float:
    """Calculate demographic parity difference (DPD)."""
    y_pred_arr = np.array(y_pred)
    protected = np.array(protected_attribute)
    
    privileged_mask = protected == privileged_group
    if privileged_mask.sum() == 0:
        pr_privileged = 0.0
    else:
        pr_privileged = y_pred_arr[privileged_mask].mean()
    
    unprivileged_mask = protected == unprivileged_group
    if unprivileged_mask.sum() == 0:
        pr_unprivileged = 0.0
    else:
        pr_unprivileged = y_pred_arr[unprivileged_mask].mean()
    
    return pr_unprivileged - pr_privileged


def statistical_parity_difference(
    y_pred: Sequence[int],
    protected_attribute: Sequence[int],
    privileged_group: int = 1,
    unprivileged_group: int = 0
) -> float:
    """Calculate statistical parity difference (alias for DPD)."""
    return demographic_parity_difference(y_pred, protected_attribute, privileged_group, unprivileged_group)


def calculate_all_fairness_metrics(
    y_true: Sequence[int],
    y_pred: Sequence[int],
    protected_attribute: Sequence[int],
    privileged_group: int = 1,
    unprivileged_group: int = 0
) -> dict:
    """Calculate all fairness metrics at once."""
    return {
        "disparate_impact_ratio": disparate_impact_ratio(
            y_true, y_pred, protected_attribute, privileged_group, unprivileged_group
        ),
        "equal_opportunity_difference": equal_opportunity_difference(
            y_true, y_pred, protected_attribute, privileged_group, unprivileged_group
        ),
        "demographic_parity_difference": demographic_parity_difference(
            y_pred, protected_attribute, privileged_group, unprivileged_group
        ),
        "statistical_parity_difference": statistical_parity_difference(
            y_pred, protected_attribute, privileged_group, unprivileged_group
        ),
    }


def check_fairness_thresholds(
    metrics: dict,
    dir_threshold: float = 0.8,
    eod_threshold: float = 0.1,
    dpd_threshold: float = 0.1
) -> dict:
    """Check if fairness metrics meet acceptable thresholds."""
    dir_value = metrics.get("disparate_impact_ratio", 0.0)
    eod_value = abs(metrics.get("equal_opportunity_difference", 0.0))
    dpd_value = abs(metrics.get("demographic_parity_difference", 0.0))
    
    return {
        "disparate_impact_ratio_pass": dir_value >= dir_threshold,
        "equal_opportunity_difference_pass": eod_value <= eod_threshold,
        "demographic_parity_difference_pass": dpd_value <= dpd_threshold,
        "statistical_parity_difference_pass": dpd_value <= dpd_threshold,
    }


def generate_fairness_report(
    metrics: dict,
    checks: dict,
    protected_attribute_name: str = "protected",
    privileged_group_name: str = "privileged",
    unprivileged_group_name: str = "unprivileged",
    sample_size: int = 0
) -> str:
    """Generate a human-readable fairness report."""
    report = []
    report.append("=" * 60)
    report.append("FAIRNESS & BIAS DETECTION REPORT")
    report.append("=" * 60)
    report.append(f"Protected Attribute: {protected_attribute_name}")
    report.append(f"Privileged Group: {privileged_group_name}")
    report.append(f"Unprivileged Group: {unprivileged_group_name}")
    if sample_size > 0:
        report.append(f"Sample Size: {sample_size}")
    report.append("")
    
    report.append("METRICS:")
    report.append(f"  Disparate Impact Ratio: {metrics.get('disparate_impact_ratio', 0.0):.4f}")
    report.append(f"  Equal Opportunity Difference: {metrics.get('equal_opportunity_difference', 0.0):.4f}")
    report.append(f"  Demographic Parity Difference: {metrics.get('demographic_parity_difference', 0.0):.4f}")
    report.append(f"  Statistical Parity Difference: {metrics.get('statistical_parity_difference', 0.0):.4f}")
    report.append("")
    
    report.append("THRESHOLD CHECKS:")
    for metric, passed in checks.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        report.append(f"  {metric}: {status}")
    report.append("")
    
    all_passed = all(checks.values())
    if all_passed:
        report.append("OVERALL ASSESSMENT: ✅ NO BIAS DETECTED")
    else:
        report.append("OVERALL ASSESSMENT: ⚠️ BIAS DETECTED")
        report.append("The model shows potential bias against the unprivileged group.")
        report.append("Consider reviewing training data, feature selection, or model architecture.")
    
    report.append("=" * 60)
    
    return "\n".join(report)


def export_fairness_report_json(
    metrics: dict,
    checks: dict,
    protected_attribute_name: str = "protected",
    sample_size: int = 0
) -> str:
    """Export fairness report as JSON string."""
    import json
    
    report_dict = {
        "protected_attribute": protected_attribute_name,
        "sample_size": sample_size,
        "metrics": metrics,
        "threshold_checks": checks,
        "overall_fair": all(checks.values()),
    }
    
    return json.dumps(report_dict, indent=2)
