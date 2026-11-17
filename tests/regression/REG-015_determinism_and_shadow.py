import uuid

from trust_net_port.schema.contracts import AgentProposal, OutcomeEnum
from trust_net_port.validator import PortValidator


def test_determinism():
    validator = PortValidator()
    proposal = AgentProposal(
        proposal_id="P-DET-01",
        case_id="C-DET-01",
        action="approve",
        amount=10000.0,
        term_months=12,
        dsti_ratio=0.30,
        facts_cited=["F-1", "F-2", "F-3"],
        correlation_id="fixed-uuid-for-determinism-test",
    )
    r1 = validator.validate(proposal).model_dump_json(exclude={"evaluated_at"})
    r2 = validator.validate(proposal).model_dump_json(exclude={"evaluated_at"})
    assert r1 == r2


def test_shadow_mode_negative_proof():
    validator = PortValidator()
    validator.set_shadow_mode(True)
    proposal = AgentProposal(
        proposal_id="P-SH-NEG",
        case_id="C-SH-NEG",
        action="approve",
        amount=10000.0,
        term_months=12,
        dsti_ratio=0.50,
        facts_cited=["F-1", "F-2", "F-3"],
    )
    result = validator.validate(proposal)
    assert result.outcome == OutcomeEnum.REFUSED
    assert result.shadow_outcome == "REFUSED"


def test_missing_correlation_id_generates_uuid():
    validator = PortValidator()
    proposal = AgentProposal(
        proposal_id="P-UUID-01", case_id="C-UUID-01", action="approve", amount=10000.0, term_months=12, dsti_ratio=0.30, facts_cited=["F-1"]
    )
    result = validator.validate(proposal)
    assert result.correlation_id != "UNKNOWN"
    uuid.UUID(result.correlation_id, version=4)
