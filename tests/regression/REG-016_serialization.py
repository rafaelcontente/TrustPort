import pytest
from pydantic import ValidationError

from trust_net_port.schema.contracts import AgentProposal, PortResult
from trust_net_port.validator import PortValidator


def test_port_result_serialization():
    """PortResult must serialize and deserialize cleanly to/from JSON."""
    validator = PortValidator()
    proposal = AgentProposal(
        proposal_id="P-SER-01", case_id="C-SER-01", action="approve",
        amount=10000.0, term_months=12, dsti_ratio=30.0, facts_cited=["F-1", "F-2", "F-3"]
    )
    result = validator.validate(proposal)
    json_str = result.model_dump_json()
    
    # Parse back
    parsed = PortResult.model_validate_json(json_str)
    assert parsed.outcome == result.outcome
    assert parsed.gates_passed == result.gates_passed

def test_invalid_enum_handling():
    """Pydantic must reject invalid enum values."""
    with pytest.raises(ValidationError): # Pydantic ValidationError
        PortResult(
            outcome="INVALID_OUTCOME",
            reason_code="TEST",
            gates_passed=[],
            gates_failed=[]
        )
