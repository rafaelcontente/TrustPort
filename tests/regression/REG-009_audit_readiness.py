import uuid
from datetime import datetime

from trust_net_port.schema.contracts import AgentProposal
from trust_net_port.validator import PortValidator


def test_audit_readiness_fields_are_populated():
    validator = PortValidator()
    proposal = AgentProposal(
        proposal_id="P-AUD-01",
        case_id="C-AUD-01",
        action="approve",
        amount=10000.0,
        term_months=12,
        dsti_ratio=0.30,
        facts_cited=["F-1", "F-2", "F-3"],
        correlation_id="trace-abc-123",
    )
    result = validator.validate(proposal)
    assert result.correlation_id == "trace-abc-123"
    assert result.evaluated_at is not None
    parsed_dt = datetime.fromisoformat(result.evaluated_at)
    assert parsed_dt.tzinfo is not None


def test_audit_readiness_generates_uuid_when_missing():
    validator = PortValidator()
    proposal = AgentProposal(
        proposal_id="P-AUD-02", case_id="C-AUD-02", action="approve", amount=10000.0, term_months=12, dsti_ratio=0.30, facts_cited=["F-1"]
    )
    result = validator.validate(proposal)
    assert result.correlation_id != "UNKNOWN"
    uuid.UUID(result.correlation_id, version=4)
