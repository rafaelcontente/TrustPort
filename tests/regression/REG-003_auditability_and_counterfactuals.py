from trust_net_port.schema.contracts import AgentProposal, OutcomeEnum
from trust_net_port.validator import PortValidator


def test_refusal_contains_concrete_reasons():
    proposal = AgentProposal(
        proposal_id="P-004", case_id="C-0145", action="approve", amount=50000, term_months=60, dsti_ratio=0.45, facts_cited=["F-221"]
    )
    result = PortValidator().validate(proposal)
    assert result.outcome == OutcomeEnum.REFUSED
    assert result.explanation is not None
    assert "exceeds policy limit" in result.explanation


def test_counterfactual_is_actionable():
    proposal = AgentProposal(
        proposal_id="P-005", case_id="C-0146", action="approve", amount=50000, term_months=60, dsti_ratio=0.45, facts_cited=["F-221"]
    )
    result = PortValidator().validate(proposal)
    assert result.counterfactual is not None
    assert "40.0%" in result.counterfactual or "Reduce" in result.counterfactual
