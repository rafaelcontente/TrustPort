"""Tests for the dynamic Policy Manager."""
from trust_net_port.policy_manager import PolicyManager


def test_policy_manager_get_existing_key():
    """Test retrieving an existing policy key."""
    pm = PolicyManager(policy_path="src/trust_net_port/policy.yaml")
    assert pm.get("max_dsti_ratio") == 0.40
    assert pm.get("min_amount") == 500.0


def test_policy_manager_get_default_value():
    """Test retrieving a non-existent key returns the default."""
    pm = PolicyManager(policy_path="src/trust_net_port/policy.yaml")
    assert pm.get("non_existent_key", "default_val") == "default_val"
    assert pm.get("another_missing") is None
