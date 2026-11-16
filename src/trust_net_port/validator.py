from datetime import datetime, timezone
import json
from pathlib import Path
from .schema.contracts import AgentProposal, PortResult, OutcomeEnum
from .solver.z3_verifier import verify_constraints

class ConformalUncertaintyEstimator:
    def __init__(self, base_uncertainty: float = 2.5):
        self.base_uncertainty = base_uncertainty

    def calculate_upper_bound(self, proposal: AgentProposal) -> float:
        # Heuristic penalty for missing facts
        fact_penalty = max(0, (3 - len(proposal.facts_cited))) * 1.5
        # Heuristic penalty for high DSTI
        dsti_penalty = max(0, (proposal.dsti_ratio - 30.0) / 10.0) * 2.0
        return self.base_uncertainty + fact_penalty + dsti_penalty

class PortValidator:
    def __init__(self):
        self.policy_path = Path(__file__).parent / 'policy' / 'policies.json'
        with open(self.policy_path) as f:
            self.policy = json.load(f)
        self.rules = self.policy['rules']
        self.uncertainty_estimator = ConformalUncertaintyEstimator()

    def validate(self, proposal: AgentProposal) -> PortResult:
        evaluated_at = datetime.now(timezone.utc).isoformat()
        corr_id = proposal.correlation_id or "UNKNOWN"
        gates_passed = []
        gates_failed = []
        pv = self.policy["version"]

        # Gate 1: Schema
        if proposal.amount <= 0 or proposal.dsti_ratio < 0 or len(proposal.facts_cited) == 0:
            gates_failed.append("G1_SCHEMA")
            return PortResult(
                outcome=OutcomeEnum.REPAIRED,
                reason_code="SCH-01",
                gates_passed=gates_passed,
                gates_failed=gates_failed,
                explanation="Invalid schema: amount/DSTI must be positive and at least one fact must be cited.",
                policy_version=pv, evaluated_at=evaluated_at, correlation_id=corr_id
            )
        gates_passed.append("G1_SCHEMA")

        # Gate 2: Rules
        max_dsti = self.rules["max_dsti_ratio"] * 100
        if proposal.dsti_ratio > max_dsti:
            gates_failed.append("G2_RULES")
            return PortResult(
                outcome=OutcomeEnum.REFUSED,
                reason_code="RUL-01",
                gates_passed=gates_passed,
                gates_failed=gates_failed,
                counterfactual=f"Reduce DSTI to <= {max_dsti}%",
                explanation=f"DSTI ratio {proposal.dsti_ratio}% exceeds policy limit of {max_dsti}%.",
                policy_version=pv, evaluated_at=evaluated_at, correlation_id=corr_id
            )
        gates_passed.append("G2_RULES")

        # Gate 3: Z3 Solver
        is_valid, reason = verify_constraints(
            proposal, 
            self.rules["high_amount_threshold"], 
            self.rules["min_term_for_high_amount"]
        )
        if not is_valid:
            gates_failed.append("G3_SOLVER")
            return PortResult(
                outcome=OutcomeEnum.REFUSED,
                reason_code="SMT-01",
                gates_passed=gates_passed,
                gates_failed=gates_failed,
                explanation=reason,
                policy_version=pv, evaluated_at=evaluated_at, correlation_id=corr_id
            )
        gates_passed.append("G3_SOLVER")

        # Gate 4: Uncertainty (Heuristic for now, Conformal is separate module)
        upper_bound = self.uncertainty_estimator.calculate_upper_bound(proposal)
        if upper_bound > 5.0:  # Pilot threshold
            gates_failed.append("G4_UNCERTAINTY")
            return PortResult(
                outcome=OutcomeEnum.ESCALATED,
                reason_code="UNC-02",
                gates_passed=gates_passed,
                gates_failed=gates_failed,
                counterfactual="Provide more cited facts or reduce amount to lower uncertainty bound.",
                explanation=f"Uncertainty upper bound ({upper_bound}%) exceeds pilot threshold (5.0%).",
                policy_version=pv, evaluated_at=evaluated_at, correlation_id=corr_id
            )
        gates_passed.append("G4_UNCERTAINTY")

        # Gate 5: Explanation (Pass-through for now)
        gates_passed.append("G5_FIDELITY")

        return PortResult(
            outcome=OutcomeEnum.APPROVED,
            reason_code="OK-00",
            gates_passed=gates_passed,
            gates_failed=gates_failed,
            explanation="Proposal meets all schema, rule, formal, and uncertainty criteria.",
            policy_version=pv, evaluated_at=evaluated_at, correlation_id=corr_id
        )
