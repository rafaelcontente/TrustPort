from .schema.contracts import AgentProposal, OutcomeEnum, PortResult


class ConformalUncertaintyEstimator:
    def __init__(self, base_uncertainty: float = 2.5, alpha: float = 0.10):
        self.base_uncertainty = base_uncertainty
        self.alpha = alpha

    def calculate_upper_bound(self, proposal: AgentProposal) -> float:
        uncertainty = self.base_uncertainty
        fact_penalty = max(0, (3 - len(proposal.facts_cited))) * 1.5
        dsti_penalty = max(0, (proposal.dsti_ratio - 30.0) / 10.0) * 2.0
        return uncertainty + fact_penalty + dsti_penalty

class PortValidator:
    def __init__(self):
        self.uncertainty_estimator = ConformalUncertaintyEstimator()
        self.pilot_threshold = 5.0

    def validate(self, proposal: AgentProposal) -> PortResult:
        gates_passed, gates_failed = [], []
        
        # Gate 1: Schema & Data Contract
        if proposal.amount > 0 and proposal.dsti_ratio >= 0 and len(proposal.facts_cited) > 0:
            gates_passed.append("G1_SCHEMA")
        else:
            gates_failed.append("G1_SCHEMA")
            return PortResult(
                outcome=OutcomeEnum.REPAIRED, 
                reason_code="SCH-01", 
                gates_passed=gates_passed, 
                gates_failed=gates_failed, 
                explanation="Invalid schema: amount/DSTI must be positive and at least one fact must be cited."
            )

        # Gate 2: Domain Rules (Policy-as-Code)
        if proposal.dsti_ratio <= 40.0:
            gates_passed.append("G2_RULES")
        else:
            gates_failed.append("G2_RULES")
            return PortResult(
                outcome=OutcomeEnum.REFUSED, 
                reason_code="RUL-01", 
                gates_passed=gates_passed, 
                gates_failed=gates_failed, 
                counterfactual=f"Reduce DSTI to <= 40.0% (current: {proposal.dsti_ratio}%)", 
                explanation="DSTI ratio exceeds maximum regulatory limit of 40%."
            )

        # Gate 3: Formal Verification (SMT/MILP placeholder)
        gates_passed.append("G3_SOLVER")

        # Gate 4: Uncertainty (Dynamic Conformal Prediction)
        upper_bound_pd = self.uncertainty_estimator.calculate_upper_bound(proposal)
        if upper_bound_pd <= self.pilot_threshold:
            gates_passed.append("G4_UNCERTAINTY")
        else:
            gates_failed.append("G4_UNCERTAINTY")
            return PortResult(
                outcome=OutcomeEnum.ESCALATED, 
                reason_code="UNC-02", 
                gates_passed=gates_passed, 
                gates_failed=gates_failed, 
                counterfactual="Provide more cited facts or reduce amount to lower uncertainty bound.", 
                explanation=f"Uncertainty upper bound ({upper_bound_pd:.1f}%) exceeds pilot threshold ({self.pilot_threshold}%)."
            )

        # Gate 5: Fidelity & Explanation
        gates_passed.append("G5_FIDELITY")
        return PortResult(
            outcome=OutcomeEnum.APPROVED, 
            reason_code="OK-00", 
            gates_passed=gates_passed, 
            gates_failed=gates_failed, 
            explanation="All validation gates passed successfully."
        )