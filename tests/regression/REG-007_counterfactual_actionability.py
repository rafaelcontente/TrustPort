from trust_net_port.schema.contracts import AgentProposal, OutcomeEnum
from trust_net_port.validator import PortValidator


def test_counterfactual_mutation_proves_actionability():
    """
    Proves that applying the suggested counterfactual actually flips the outcome
    from REFUSED to APPROVED, satisfying the 'actionable' requirement.
    """
    validator = PortValidator()

    # 1. Original proposal that fails ONLY on G2 (DSTI > 40%)
    # Amount is 30k (safe for G3), term is 24 (safe for G3).
    original_proposal = AgentProposal(
        proposal_id="P-CF-01",
        case_id="C-CF-01",
        action="approve",
        amount=30000.0,
        term_months=24,
        dsti_ratio=0.45,  # Violates G2 (limit is 40%)
        facts_cited=["F-100", "F-101", "F-102"],
    )

    # 2. Validate and assert REFUSED with counterfactual
    result = validator.validate(original_proposal)
    assert result.outcome == OutcomeEnum.REFUSED
    assert result.reason_code == "RUL-01"
    assert result.counterfactual is not None
    assert "40%" in result.counterfactual  # e.g., "Reduce DSTI to <= 40.0%"

    # 3. Mutate the proposal based on the counterfactual
    # We apply a safe value (39.0%) to satisfy the rule.
    mutated_proposal = AgentProposal(
        proposal_id=original_proposal.proposal_id,
        case_id=original_proposal.case_id,
        action=original_proposal.action,
        amount=original_proposal.amount,
        term_months=original_proposal.term_months,
        dsti_ratio=0.39,  # Mutated to satisfy the counterfactual
        facts_cited=original_proposal.facts_cited,
    )

    # 4. Re-validate the mutated proposal
    new_result = validator.validate(mutated_proposal)

    # 5. Assert the outcome flipped to APPROVED
    assert new_result.outcome == OutcomeEnum.APPROVED, f"Expected APPROVED, got {new_result.outcome}"
    assert new_result.reason_code == "OK-00"
    assert "G1_SCHEMA" in new_result.gates_passed
    assert "G2_RULES" in new_result.gates_passed
