"""
Bias Detection Demo
===================
This script demonstrates how to use TrustPort's fairness module
to detect bias in AI-mediated decisions.

It generates synthetic data with and without bias, calculates
fairness metrics, and generates reports.

Run this script to see bias detection in action.
"""

import numpy as np

from trust_net_port.fairness.metrics import calculate_all_fairness_metrics, check_fairness_thresholds
from trust_net_port.fairness.report import export_fairness_report_json, generate_fairness_report

print("=" * 80)
print("BIAS DETECTION DEMO")
print("=" * 80)


# ============================================================================
# SCENARIO 1: FAIR DATA (No Bias)
# ============================================================================

print("\n" + "=" * 80)
print("SCENARIO 1: FAIR DATA (No Bias)")
print("=" * 80)

print("\n[1/3] Generating synthetic fair data...")
np.random.seed(42)
n_samples = 1000

# Protected attribute: 50% privileged (1), 50% unprivileged (0)
protected_attribute = np.random.choice([0, 1], size=n_samples, p=[0.5, 0.5])

# Ground truth: 50% positive for both groups (fair)
y_true = np.random.choice([0, 1], size=n_samples, p=[0.5, 0.5])

# Predictions: 50% positive for both groups (fair)
y_pred = np.random.choice([0, 1], size=n_samples, p=[0.5, 0.5])

print(f"      Sample size: {n_samples}")
print(f"      Privileged group: {protected_attribute.sum()} samples")
print(f"      Unprivileged group: {n_samples - protected_attribute.sum()} samples")

print("[2/3] Calculating fairness metrics...")
metrics = calculate_all_fairness_metrics(y_true.tolist(), y_pred.tolist(), protected_attribute.tolist())
checks = check_fairness_thresholds(metrics)

print("[3/3] Generating fairness report...")
report = generate_fairness_report(
    metrics=metrics,
    checks=checks,
    protected_attribute_name="gender",
    privileged_group_name="male",
    unprivileged_group_name="female",
    sample_size=n_samples,
)
print(report)


# ============================================================================
# SCENARIO 2: BIASED DATA (Bias Against Unprivileged Group)
# ============================================================================

print("\n" + "=" * 80)
print("SCENARIO 2: BIASED DATA (Bias Against Unprivileged Group)")
print("=" * 80)

print("\n[1/3] Generating synthetic biased data...")
np.random.seed(123)
n_samples = 1000

# Protected attribute: 50% privileged (1), 50% unprivileged (0)
protected_attribute = np.random.choice([0, 1], size=n_samples, p=[0.5, 0.5])

# Ground truth: 50% positive for both groups
y_true = np.random.choice([0, 1], size=n_samples, p=[0.5, 0.5])

# Predictions: 80% positive for privileged, 20% positive for unprivileged (BIASED)
y_pred = np.where(
    protected_attribute == 1, np.random.choice([0, 1], size=n_samples, p=[0.8, 0.2]), np.random.choice([0, 1], size=n_samples, p=[0.2, 0.8])
)

print(f"      Sample size: {n_samples}")
print(f"      Privileged group positive rate: {y_pred[protected_attribute == 1].mean():.2%}")
print(f"      Unprivileged group positive rate: {y_pred[protected_attribute == 0].mean():.2%}")

print("[2/3] Calculating fairness metrics...")
metrics = calculate_all_fairness_metrics(y_true.tolist(), y_pred.tolist(), protected_attribute.tolist())
checks = check_fairness_thresholds(metrics)

print("[3/3] Generating fairness report...")
report = generate_fairness_report(
    metrics=metrics,
    checks=checks,
    protected_attribute_name="race",
    privileged_group_name="group_a",
    unprivileged_group_name="group_b",
    sample_size=n_samples,
)
print(report)


# ============================================================================
# SCENARIO 3: EXPORT TO JSON
# ============================================================================

print("\n" + "=" * 80)
print("SCENARIO 3: EXPORT FAIRNESS REPORT TO JSON")
print("=" * 80)

print("\n[1/1] Exporting fairness report as JSON...")
json_report = export_fairness_report_json(metrics=metrics, checks=checks, protected_attribute_name="race", sample_size=n_samples)
print(json_report)


print("\n" + "=" * 80)
print("DEMO COMPLETE")
print("=" * 80)
print("\nKey Takeaways:")
print("• Fairness metrics quantify bias in AI decisions")
print("• Disparate Impact Ratio < 0.8 indicates adverse impact")
print("• Equal Opportunity Difference > 0.1 indicates unequal TPR")
print("• Demographic Parity Difference > 0.1 indicates unequal positive rates")
print("• TrustPort provides automated bias detection for compliance with AI Act")
