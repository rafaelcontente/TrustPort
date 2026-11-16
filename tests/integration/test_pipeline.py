from trust_net_port.schema.contracts import AgentProposal, OutcomeEnum
from trust_net_port.validator import PortValidator


def test_integration_valid_proposal_passes_all_gates():
    validator = PortValidator()
    proposal = AgentProposal(
        proposal_id="P-INT-1", case_id="C-INT-1", action="approve",
        amount=30000.0, term_months=48, dsti_ratio=32.0,
        facts_cited=["F-101", "F-102", "F-103", "F-104"]
    )
    result = validator.validate(proposal)
    assert result.outcome == OutcomeEnum.APPROVED
    assert result.reason_code == "OK-00"
    assert "G1_SCHEMA" in result.gates_passed
    assert "G2_RULES" in result.gates_passed
    assert "G3_SOLVER" in result.gates_passed
    assert "G4_UNCERTAINTY" in result.gates_passed
    assert "G5_FIDELITY" in result.gates_passed

def test_integration_invalid_proposal_fails_fast():
    validator = PortValidator()
    proposal = AgentProposal(
        proposal_id="P-INT-2", case_id="C-INT-2", action="approve",
        amount=-500.0, term_months=12, dsti_ratio=10.0,
        facts_cited=[]
    )
    result = validator.validate(proposal)
    assert result.outcome == OutcomeEnum.REPAIRED
    assert result.reason_code == "SCH-01"
    assert "G1_SCHEMA" in result.gates_failed
    # Fail-fast: subsequent gates should not be evaluated/passed
    assert "G2_RULES" not in result.gates_passed
