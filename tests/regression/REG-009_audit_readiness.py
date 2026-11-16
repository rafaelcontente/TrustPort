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
        dsti_ratio=30.0,
        facts_cited=["F-1", "F-2", "F-3"],
        correlation_id="trace-abc-123"
    )
    
    result = validator.validate(proposal)
    
    # 1. Correlation ID must be propagated
    assert result.correlation_id == "trace-abc-123"
    
    # 2. evaluated_at must be a valid ISO 8601 string
    assert result.evaluated_at is not None
    # This will raise ValueError if the format is invalid
    parsed_dt = datetime.fromisoformat(result.evaluated_at)
    assert parsed_dt.tzinfo is not None  # Must be timezone-aware (UTC)

def test_audit_readiness_handles_missing_correlation_id():
    validator = PortValidator()
    proposal = AgentProposal(
        proposal_id="P-AUD-02", case_id="C-AUD-02", action="approve",
        amount=10000.0, term_months=12, dsti_ratio=30.0, facts_cited=["F-1"]
        # correlation_id omitted
    )
    result = validator.validate(proposal)
    assert result.correlation_id == "UNKNOWN"
    assert result.evaluated_at is not None
