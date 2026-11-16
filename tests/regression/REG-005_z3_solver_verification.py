from trust_net_port.schema.contracts import AgentProposal, OutcomeEnum
from trust_net_port.validator import PortValidator


def test_g3_z3_passes_valid_high_amount_with_long_term():
    # Amount > 50k, but term >= 36. G2 passes (DSTI 30%), G3 should PASS.
    proposal = AgentProposal(
        proposal_id="P-Z3-01", case_id="C-Z3-01", action="approve",
        amount=60000.0, term_months=48, dsti_ratio=30.0,
        facts_cited=["F-100", "F-101", "F-102"]
    )
    result = PortValidator().validate(proposal)
    assert result.outcome == OutcomeEnum.APPROVED
    assert "G3_SOLVER" in result.gates_passed

def test_g3_z3_rejects_what_g2_allows():
    # Amount > 50k AND term < 36. G2 PASSES (DSTI 30% <= 40%), but G3 MUST REJECT.
    proposal = AgentProposal(
        proposal_id="P-Z3-02", case_id="C-Z3-02", action="approve",
        amount=60000.0, term_months=12, dsti_ratio=30.0,
        facts_cited=["F-100", "F-101", "F-102"]
    )
    result = PortValidator().validate(proposal)
    assert result.outcome == OutcomeEnum.REFUSED
    assert result.reason_code == "SMT-01"
    assert "G3_SOLVER" in result.gates_failed
    assert "SMT-01" in result.reason_code and "formal constraints" in result.explanation
