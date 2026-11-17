from trust_net_port.schema.contracts import AgentProposal, OutcomeEnum
from trust_net_port.validator import PortValidator


def test_shadow_mode_never_alters_primary_outcome():
    """Shadow mode must observe, NEVER change a REFUSED/ESCALATED decision to APPROVED."""
    validator = PortValidator()
    validator.set_shadow_mode(True)

    # Proposal that fails G2 (DSTI 50% > 40%)
    proposal = AgentProposal(
        proposal_id="P-SHADOW-01",
        case_id="C-SHADOW-01",
        action="approve",
        amount=10000.0,
        term_months=12,
        dsti_ratio=0.50,
        facts_cited=["F-1", "F-2", "F-3"],
    )
    result = validator.validate(proposal)

    # Primary outcome MUST remain REFUSED
    assert result.outcome == OutcomeEnum.REFUSED
    assert result.reason_code == "RUL-01"

    # Shadow fields record the decision for audit
    assert result.shadow_outcome == "REFUSED"
    assert result.shadow_reason_code == "RUL-01"


def test_shadow_mode_approved_remains_approved():
    validator = PortValidator()
    validator.set_shadow_mode(True)
    proposal = AgentProposal(
        proposal_id="P-SHADOW-02",
        case_id="C-SHADOW-02",
        action="approve",
        amount=10000.0,
        term_months=12,
        dsti_ratio=0.30,
        facts_cited=["F-1", "F-2", "F-3"],
    )
    result = validator.validate(proposal)
    assert result.outcome == OutcomeEnum.APPROVED
    assert result.shadow_outcome == "APPROVED"
