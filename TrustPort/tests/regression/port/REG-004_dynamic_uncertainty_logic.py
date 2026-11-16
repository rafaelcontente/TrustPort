import pytest
from trust_net_port.schema.contracts import AgentProposal, OutcomeEnum
from trust_net_port.validator import PortValidator

def test_high_quality_proposal_passes_uncertainty_gate():
    proposal = AgentProposal(proposal_id="P-100", case_id="C-TEST", action="approve", amount=40000, term_months=60, dsti_ratio=25.0, facts_cited=["F-221", "F-222", "F-223"])
    result = PortValidator().validate(proposal)
    assert result.outcome == OutcomeEnum.APPROVED
    assert "G4_UNCERTAINTY" in result.gates_passed

def test_low_quality_proposal_triggers_escalation():
    proposal = AgentProposal(proposal_id="P-101", case_id="C-TEST", action="approve", amount=40000, term_months=60, dsti_ratio=38.0, facts_cited=["F-221"])
    result = PortValidator().validate(proposal)
    assert result.outcome == OutcomeEnum.ESCALATED
    assert result.reason_code == "UNC-02"
    assert "G4_UNCERTAINTY" in result.gates_failed
