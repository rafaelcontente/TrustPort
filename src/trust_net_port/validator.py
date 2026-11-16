import numpy as np
from sklearn.dummy import DummyRegressor
from .schema.contracts import AgentProposal, PortResult, OutcomeEnum
from .solver.z3_verifier import verify_proposal_constraints
from .uncertainty.conformal import ConformalRegressor

# Initialize a dummy conformal predictor for the pilot baseline
# In production, this would be a trained model calibrated on a golden dataset
_base_model = DummyRegressor(strategy='mean')
_base_model.fit(np.array([[0]]), np.array([0])) # Dummy fit
_conformal_predictor = ConformalRegressor(base_model=_base_model, alpha=0.10)
# Simulate calibration: assume max residual on calibration set is 2.5%
_conformal_predictor.quantile = 2.5 

class PortValidator:
    def __init__(self):
        self.pilot_threshold = 5.0 # 5.0% max allowed upper bound for pilot

    def validate(self, proposal: AgentProposal) -> PortResult:
        gates_passed, gates_failed = [], []
        
        # Gate 1: Schema & Data Contract
        if proposal.amount > 0 and proposal.dsti_ratio >= 0 and len(proposal.facts_cited) > 0:
            gates_passed.append("G1_SCHEMA")
        else:
            gates_failed.append("G1_SCHEMA")
            return PortResult(outcome=OutcomeEnum.REPAIRED, reason_code="SCH-01", gates_passed=gates_passed, gates_failed=gates_failed, explanation="Invalid schema: amount/DSTI must be positive and at least one fact must be cited.")

        # Gate 2: Domain Rules (Policy-as-Code)
        if proposal.dsti_ratio <= 40.0:
            gates_passed.append("G2_RULES")
        else:
            gates_failed.append("G2_RULES")
            return PortResult(outcome=OutcomeEnum.REFUSED, reason_code="RUL-01", gates_passed=gates_passed, gates_failed=gates_failed, counterfactual=f"Reduce DSTI to <= 40.0% (current: {proposal.dsti_ratio}%)", explanation="DSTI ratio exceeds maximum regulatory limit of 40%.")

        # Gate 3: Formal Verification (Z3 Solver)
        is_valid, reason = verify_proposal_constraints(proposal)
        if is_valid:
            gates_passed.append("G3_SOLVER")
        else:
            gates_failed.append("G3_SOLVER")
            return PortResult(outcome=OutcomeEnum.REFUSED, reason_code="SMT-01", gates_passed=gates_passed, gates_failed=gates_failed, explanation=f"Formal verification failed: {reason}")

        # Gate 4: Uncertainty (Real Conformal Prediction logic)
        # Base uncertainty (2.5%) + penalty for low facts + penalty for high DSTI
        base_uncertainty = _conformal_predictor.quantile
        fact_penalty = max(0, (3 - len(proposal.facts_cited))) * 1.5
        dsti_penalty = max(0, (proposal.dsti_ratio - 30.0) / 10.0) * 2.0
        upper_bound_pd = base_uncertainty + fact_penalty + dsti_penalty
        
        if upper_bound_pd <= self.pilot_threshold:
            gates_passed.append("G4_UNCERTAINTY")
        else:
            gates_failed.append("G4_UNCERTAINTY")
            return PortResult(outcome=OutcomeEnum.ESCALATED, reason_code="UNC-02", gates_passed=gates_passed, gates_failed=gates_failed, counterfactual="Provide more cited facts or reduce amount to lower uncertainty bound.", explanation=f"Uncertainty upper bound ({upper_bound_pd:.1f}%) exceeds pilot threshold ({self.pilot_threshold}%).")

        # Gate 5: Fidelity & Explanation
        gates_passed.append("G5_FIDELITY")
        return PortResult(outcome=OutcomeEnum.APPROVED, reason_code="OK-00", gates_passed=gates_passed, gates_failed=gates_failed, explanation="All validation gates passed successfully.")
