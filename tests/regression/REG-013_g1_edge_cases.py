from trust_net_port.schema.contracts import AgentProposal, OutcomeEnum
from trust_net_port.validator import PortValidator


def test_g1_rejects_zero_and_negative_dsti():
    validator = PortValidator()
    for bad_dsti in [0.0, -5.0]:
        proposal = AgentProposal(
            proposal_id="P-G1-01",
            case_id="C-G1-01",
            action="approve",
            amount=10000.0,
            term_months=12,
            dsti_ratio=bad_dsti,
            facts_cited=["F-1"],
        )
        result = validator.validate(proposal)
        assert result.outcome == OutcomeEnum.REPAIRED
        assert "DSTI > 0" in result.explanation


def test_g1_rejects_nan_and_inf():
    validator = PortValidator()
    for bad_amount in [float("nan"), float("inf")]:
        proposal = AgentProposal(
            proposal_id="P-G1-02",
            case_id="C-G1-02",
            action="approve",
            amount=bad_amount,
            term_months=12,
            dsti_ratio=0.30,
            facts_cited=["F-1"],
        )
        result = validator.validate(proposal)
        assert result.outcome == OutcomeEnum.REPAIRED
