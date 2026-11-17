import os
from unittest.mock import patch

import pytest

from trust_net_port.schema.contracts import AgentProposal, OutcomeEnum
from trust_net_port.validator import PortValidator


def test_fail_closed_z3_exception():
    """Z3 exception must result in REFUSED, never APPROVED."""
    validator = PortValidator()
    proposal = AgentProposal(
        proposal_id="P-FC-01",
        case_id="C-FC-01",
        action="approve",
        amount=60000.0,
        term_months=48,
        dsti_ratio=0.30,
        facts_cited=["F-1", "F-2", "F-3"],
    )
    with patch("trust_net_port.validator.verify_constraints", side_effect=RuntimeError("Z3 Crash")):
        result = validator.validate(proposal)
        assert result.outcome == OutcomeEnum.REFUSED
        assert result.reason_code == "SMT-ERR"


def test_fail_closed_missing_policy():
    """Missing policy file must prevent validator instantiation (fail-closed)."""
    validator = PortValidator()
    policy_path = validator.policy_path
    backup_name = policy_path.name + ".bak"

    try:
        os.rename(policy_path, policy_path.parent / backup_name)
        with pytest.raises(FileNotFoundError):
            PortValidator()  # Should crash, not fallback to APPROVED
    finally:
        os.rename(policy_path.parent / backup_name, policy_path)
