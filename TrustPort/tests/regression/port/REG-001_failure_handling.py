import pytest
from trust_net_port.schema.contracts import AgentProposal, OutcomeEnum
from trust_net_port.validator import PortValidator

def test_invalid_schema_is_repaired():
    proposal = AgentProposal(proposal_id="P-001", case_id="C-0142", action="approve", amount=-100, term_months=60, dsti_ratio=30.0, facts_cited=["F-221"])
    result = PortValidator().validate(proposal)
    assert result.outcome == OutcomeEnum.REPAIRED
    assert result.reason_code == "SCH-01"

def test_rule_violation_is_refused_with_counterfactual():
    proposal = AgentProposal(proposal_id="P-002", case_id="C-0143", action="approve", amount=50000, term_months=60, dsti_ratio=45.0, facts_cited=["F-221"])
    result = PortValidator().validate(proposal)
    assert result.outcome == OutcomeEnum.REFUSED
    assert result.reason_code == "RUL-01"
    assert result.counterfactual is not None

def test_100_percent_invalid_proposals_blocked():
    validator = PortValidator()
    invalid_proposals = (
        [AgentProposal(proposal_id=f"P-{i}", case_id="C-TEST", action="approve", amount=-10, term_months=60, dsti_ratio=30.0, facts_cited=[]) for i in range(50)] +
        [AgentProposal(proposal_id=f"P-{i+100}", case_id="C-TEST", action="approve", amount=50000, term_months=60, dsti_ratio=50.0, facts_cited=[]) for i in range(50)]
    )
    approved_count = sum(1 for p in invalid_proposals if validator.validate(p).outcome == OutcomeEnum.APPROVED)
    assert approved_count == 0, "Zero invalid proposals must be approved."
