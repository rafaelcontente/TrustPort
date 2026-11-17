import pytest
from pydantic import ValidationError

from trust_net_port.schema.contracts import AgentProposal, PortResult
from trust_net_port.validator import PortValidator


def test_port_result_gates_mutually_exclusive_and_unique():
    validator = PortValidator()
    # Testar aprovação
    p1 = AgentProposal(
        proposal_id="P8", case_id="C8", action="approve", amount=10000, term_months=12, dsti_ratio=0.30, facts_cited=["F1", "F2", "F3"]
    )
    r1 = validator.validate(p1)
    assert len(set(r1.gates_passed)) == len(r1.gates_passed), "Duplicates in gates_passed"
    assert len(set(r1.gates_failed)) == len(r1.gates_failed), "Duplicates in gates_failed"
    assert set(r1.gates_passed).isdisjoint(r1.gates_failed), "Gates passed and failed are not mutually exclusive"

    # Testar recusa
    p2 = AgentProposal(
        proposal_id="P9", case_id="C9", action="approve", amount=10000, term_months=12, dsti_ratio=0.50, facts_cited=["F1", "F2", "F3"]
    )
    r2 = validator.validate(p2)
    assert set(r2.gates_passed).isdisjoint(r2.gates_failed)


def test_port_result_invalid_enum_rejected():
    with pytest.raises(ValidationError):
        PortResult(outcome="INVALID_OUTCOME", reason_code="TEST", gates_passed=[], gates_failed=[])
