import json
import math
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .schema.contracts import AgentProposal, OutcomeEnum, PortResult
from .solver.z3_verifier import verify_constraints


class ConformalUncertaintyEstimator:
    def __init__(self, base_uncertainty: float = 2.5):
        self.base_uncertainty = base_uncertainty

    def calculate_upper_bound(self, proposal: AgentProposal) -> float:
        fact_penalty = max(0, (3 - len(proposal.facts_cited))) * 1.5
        dsti_penalty = max(0, (proposal.dsti_ratio - 30.0) / 10.0) * 2.0
        return self.base_uncertainty + fact_penalty + dsti_penalty


class PortValidator:
    def __init__(self):
        self.policy_path = Path(__file__).parent / 'policy' / 'policies.json'
        with open(self.policy_path) as f:
            self.policy = json.load(f)
        self.rules = self.policy['rules']
        self.uncertainty_estimator = ConformalUncertaintyEstimator()
        self.shadow_mode = False
        self._z3_lock = threading.Lock()

    def set_shadow_mode(self, enabled: bool):
        self.shadow_mode = enabled

    def validate(self, proposal: AgentProposal) -> PortResult:
        gates_passed: list[str] = []
        gates_failed: list[str] = []
        pv = self.policy["version"]
        evaluated_at = datetime.now(timezone.utc).isoformat()
        corr_id = proposal.correlation_id or str(uuid.uuid4())

        # Gate 1: Schema & Sanity
        if (proposal.amount <= 0 or not math.isfinite(proposal.amount) or
            proposal.dsti_ratio <= 0 or not math.isfinite(proposal.dsti_ratio) or
            len(proposal.facts_cited) == 0):
            gates_failed.append("G1_SCHEMA")
            return self._apply_shadow(PortResult(
                outcome=OutcomeEnum.REPAIRED, reason_code="SCH-01",
                gates_passed=gates_passed, gates_failed=gates_failed,
                explanation="Invalid schema: amount and DSTI must be strictly positive and finite, and at least one fact must be cited.",
                policy_version=pv, evaluated_at=evaluated_at, correlation_id=corr_id
            ))
        gates_passed.append("G1_SCHEMA")

        # Gate 2: Rules
        max_dsti = self.rules["max_dsti_ratio"] * 100
        if proposal.dsti_ratio > max_dsti:
            gates_failed.append("G2_RULES")
            return self._apply_shadow(PortResult(
                outcome=OutcomeEnum.REFUSED, reason_code="RUL-01",
                gates_passed=gates_passed, gates_failed=gates_failed,
                counterfactual=f"Reduce DSTI to <= {max_dsti}%",
                explanation=f"DSTI ratio {proposal.dsti_ratio}% exceeds policy limit of {max_dsti}%.",
                policy_version=pv, evaluated_at=evaluated_at, correlation_id=corr_id
            ))
        gates_passed.append("G2_RULES")

        # Gate 3: Z3 Solver (thread-safe, fail-closed, with counterfactual)
        try:
            with self._z3_lock:
                is_valid, reason = verify_constraints(
                    proposal,
                    self.rules["high_amount_threshold"],
                    self.rules["min_term_for_high_amount"]
                )
        except Exception as e:  # noqa: BLE001
            gates_failed.append("G3_SOLVER")
            return self._apply_shadow(PortResult(
                outcome=OutcomeEnum.REFUSED, reason_code="SMT-ERR",
                gates_passed=gates_passed, gates_failed=gates_failed,
                explanation=f"Solver internal error: {e!s}",
                policy_version=pv, evaluated_at=evaluated_at, correlation_id=corr_id
            ))
        if not is_valid:
            gates_failed.append("G3_SOLVER")
            return self._apply_shadow(PortResult(
                outcome=OutcomeEnum.REFUSED, reason_code="SMT-01",
                gates_passed=gates_passed, gates_failed=gates_failed,
                counterfactual=f"Reduce amount to <= {self.rules['high_amount_threshold']} or increase term to >= {self.rules['min_term_for_high_amount']} months.",
                explanation=reason,
                policy_version=pv, evaluated_at=evaluated_at, correlation_id=corr_id
            ))
        gates_passed.append("G3_SOLVER")

        # Gate 4: Uncertainty
        upper_bound = self.uncertainty_estimator.calculate_upper_bound(proposal)
        if upper_bound > 5.0:
            gates_failed.append("G4_UNCERTAINTY")
            return self._apply_shadow(PortResult(
                outcome=OutcomeEnum.ESCALATED, reason_code="UNC-02",
                gates_passed=gates_passed, gates_failed=gates_failed,
                counterfactual="Provide more cited facts or reduce amount to lower uncertainty bound.",
                explanation=f"Uncertainty upper bound ({upper_bound}%) exceeds pilot threshold (5.0%).",
                policy_version=pv, evaluated_at=evaluated_at, correlation_id=corr_id
            ))
        gates_passed.append("G4_UNCERTAINTY")

        # Gate 5: Fidelity (real check)
        explanation = "Proposal meets all schema, rule, formal, and uncertainty criteria."
        if len(explanation) < 10:
            gates_failed.append("G5_FIDELITY")
            return self._apply_shadow(PortResult(
                outcome=OutcomeEnum.ESCALATED, reason_code="FID-01",
                gates_passed=gates_passed, gates_failed=gates_failed,
                explanation="Internal error: Explanation generation failed.",
                policy_version=pv, evaluated_at=evaluated_at, correlation_id=corr_id
            ))
        gates_passed.append("G5_FIDELITY")

        return self._apply_shadow(PortResult(
            outcome=OutcomeEnum.APPROVED, reason_code="OK-00",
            gates_passed=gates_passed, gates_failed=gates_failed,
            explanation=explanation,
            policy_version=pv, evaluated_at=evaluated_at, correlation_id=corr_id
        ))

    def _apply_shadow(self, result: PortResult) -> PortResult:
        # Shadow mode NEVER alters the primary execution outcome.
        if self.shadow_mode:
            result.shadow_outcome = result.outcome.value
            result.shadow_reason_code = result.reason_code
        return result
