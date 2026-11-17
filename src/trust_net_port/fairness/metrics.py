"""Fairness metrics for bias detection.

Implements standard metrics used in AI fairness literature:
- Disparate Impact Ratio
- Equal Opportunity Difference
- Demographic Parity Difference
- Statistical Parity Difference

References:
- Feldman et al. (2015): Certifying and removing disparate impact
- Hardt et al. (2016): Equality of opportunity in supervised learning
- EU AI Act (2024): Requirements for high-risk AI systems
"""


import numpy as np


def disparate_impact_ratio(
    y_true: list[int],
    y_pred: list[int],
    protected_attribute: list[int],
    privileged_group: int = 1,
    unprivileged_group: int = 0
) -> float:
    """Calculate disparate impact ratio (DIR).
    
    DIR = P(Y=1|A=unprivileged) / P(Y=1|A=privileged)
    
    A DIR < 0.8 indicates adverse impact against the unprivileged group.
    A DIR > 1.25 indicates adverse impact against the privileged group.
    
    Args:
        y_true: Ground truth labels (0 or 1)
        y_pred: Predicted labels (0 or 1)
        protected_attribute: Protected attribute values (0 or 1)
        privileged_group: Value indicating privileged group (default: 1)
        unprivileged_group: Value indicating unprivileged group (default: 0)
    
    Returns:
        Disparate impact ratio (float)
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    protected = np.array(protected_attribute)
    
    # Positive rate for privileged group
    privileged_mask = protected == privileged_group
    if privileged_mask.sum() == 0:
        return float('nan')
    pos_rate_privileged = y_pred[privileged_mask].mean()
    
    # Positive rate for unprivileged group
    unprivileged_mask = protected == unprivileged_group
    if unprivileged_mask.sum() == 0:
        return float('nan')
    pos_rate_unprivileged = y_pred[unprivileged_mask].mean()
    
    if pos_rate_privileged == 0:
        return float('inf') if pos_rate_unprivileged > 0 else float('nan')
    
    return pos_rate_unprivileged / pos_rate_privileged


def equal_opportunity_difference(
    y_true: list[int],
    y_pred: list[int],
    protected_attribute: list[int],
    privileged_group: int = 1,
    unprivileged_group: int = 0
) -> float:
    """Calculate equal opportunity difference.
    
    EOD = TPR(unprivileged) - TPR(privileged)
    
    TPR = True Positive Rate = P(Y=1|Y_true=1, A=group)
    
    An EOD close to 0 indicates equal opportunity.
    
    Args:
        y_true: Ground truth labels (0 or 1)
        y_pred: Predicted labels (0 or 1)
        protected_attribute: Protected attribute values (0 or 1)
        privileged_group: Value indicating privileged group
        unprivileged_group: Value indicating unprivileged group
    
    Returns:
        Equal opportunity difference (float)
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    protected = np.array(protected_attribute)
    
    # TPR for privileged group
    privileged_mask = (protected == privileged_group) & (y_true == 1)
    if privileged_mask.sum() == 0:
        tpr_privileged = float('nan')
    else:
        tpr_privileged = y_pred[privileged_mask].mean()
    
    # TPR for unprivileged group
    unprivileged_mask = (protected == unprivileged_group) & (y_true == 1)
    if unprivileged_mask.sum() == 0:
        tpr_unprivileged = float('nan')
    else:
        tpr_unprivileged = y_pred[unprivileged_mask].mean()
    
    if np.isnan(tpr_privileged) or np.isnan(tpr_unprivileged):
        return float('nan')
    
    return tpr_unprivileged - tpr_privileged


def demographic_parity_difference(
    y_pred: list[int],
    protected_attribute: list[int],
    privileged_group: int = 1,
    unprivileged_group: int = 0
) -> float:
    """Calculate demographic parity difference.
    
    DPD = P(Y=1|A=unprivileged) - P(Y=1|A=privileged)
    
    A DPD close to 0 indicates demographic parity.
    
    Args:
        y_pred: Predicted labels (0 or 1)
        protected_attribute: Protected attribute values (0 or 1)
        privileged_group: Value indicating privileged group
        unprivileged_group: Value indicating unprivileged group
    
    Returns:
        Demographic parity difference (float)
    """
    y_pred = np.array(y_pred)
    protected = np.array(protected_attribute)
    
    # Positive rate for privileged group
    privileged_mask = protected == privileged_group
    if privileged_mask.sum() == 0:
        return float('nan')
    pos_rate_privileged = y_pred[privileged_mask].mean()
    
    # Positive rate for unprivileged group
    unprivileged_mask = protected == unprivileged_group
    if unprivileged_mask.sum() == 0:
        return float('nan')
    pos_rate_unprivileged = y_pred[unprivileged_mask].mean()
    
    return pos_rate_unprivileged - pos_rate_privileged


def statistical_parity_difference(
    y_pred: list[int],
    protected_attribute: list[int],
    privileged_group: int = 1,
    unprivileged_group: int = 0
) -> float:
    """Alias for demographic_parity_difference (same metric, different name)."""
    return demographic_parity_difference(y_pred, protected_attribute, privileged_group, unprivileged_group)


def calculate_all_fairness_metrics(
    y_true: list[int],
    y_pred: list[int],
    protected_attribute: list[int],
    privileged_group: int = 1,
    unprivileged_group: int = 0
) -> dict[str, float]:
    """Calculate all fairness metrics at once.
    
    Args:
        y_true: Ground truth labels (0 or 1)
        y_pred: Predicted labels (0 or 1)
        protected_attribute: Protected attribute values (0 or 1)
        privileged_group: Value indicating privileged group
        unprivileged_group: Value indicating unprivileged group
    
    Returns:
        Dictionary with all fairness metrics
    """
    return {
        'disparate_impact_ratio': disparate_impact_ratio(
            y_true, y_pred, protected_attribute, privileged_group, unprivileged_group
        ),
        'equal_opportunity_difference': equal_opportunity_difference(
            y_true, y_pred, protected_attribute, privileged_group, unprivileged_group
        ),
        'demographic_parity_difference': demographic_parity_difference(
            y_pred, protected_attribute, privileged_group, unprivileged_group
        ),
        'statistical_parity_difference': statistical_parity_difference(
            y_pred, protected_attribute, privileged_group, unprivileged_group
        ),
    }


def check_fairness_thresholds(
    metrics: dict[str, float],
    dir_threshold: tuple[float, float] = (0.8, 1.25),
    eod_threshold: float = 0.1,
    dpd_threshold: float = 0.1
) -> dict[str, bool]:
    """Check if fairness metrics are within acceptable thresholds.
    
    Args:
        metrics: Dictionary of fairness metrics
        dir_threshold: Acceptable range for disparate impact ratio (default: 0.8-1.25)
        eod_threshold: Maximum absolute value for equal opportunity difference (default: 0.1)
        dpd_threshold: Maximum absolute value for demographic parity difference (default: 0.1)
    
    Returns:
        Dictionary indicating which metrics pass/fail thresholds
    """
    checks = {
        'disparate_impact_ratio_pass': dir_threshold[0] <= metrics['disparate_impact_ratio'] <= dir_threshold[1],
        'equal_opportunity_difference_pass': abs(metrics['equal_opportunity_difference']) <= eod_threshold,
        'demographic_parity_difference_pass': abs(metrics['demographic_parity_difference']) <= dpd_threshold,
        'statistical_parity_difference_pass': abs(metrics['statistical_parity_difference']) <= dpd_threshold,
    }
    return checks
