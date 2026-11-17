import json
import math
import re
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
        # Corrigido para formato decimal (ex: 0.45 - 0.30)
        dsti_penalty = max(0, (proposal.dsti_ratio - 0.30) / 0.10) * 2.0
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

        # Gate 1: Schema & Sanity + Policy Limits
        max_amount = self.rules.get('max_amount', 1000000.0)
        min_term = self.rules.get('min_term_months', 6)
        max_facts = self.rules.get('max_facts', 20)
        
        if (proposal.amount <= 0 or not math.isfinite(proposal.amount) or
            proposal.amount > max_amount or
            proposal.dsti_ratio <= 0 or not math.isfinite(proposal.dsti_ratio) or
            proposal.term_months < min_term or
            len(proposal.facts_cited) == 0 or
            len(proposal.facts_cited) > max_facts):
            gates_failed.append("G1_SCHEMA")
            return self._apply_shadow(PortResult(
                outcome=OutcomeEnum.REPAIRED, reason_code="SCH-01",
                gates_passed=gates_passed, gates_failed=gates_failed,
                explanation=f"Invalid schema or policy limits: amount in (0, {max_amount}], DSTI > 0, term >= {min_term}m, facts in [1, {max_facts}].",
                policy_version=pv, evaluated_at=evaluated_at, correlation_id=corr_id
            ))
        gates_passed.append("G1_SCHEMA")

        # Gate 2: Rules (CORRIGIDO: removido o * 100 para comparar decimal com decimal)
        max_dsti = self.rules["max_dsti_ratio"]  # ex: 0.40
        if proposal.dsti_ratio > max_dsti:
            gates_failed.append("G2_RULES")
            return self._apply_shadow(PortResult(
                outcome=OutcomeEnum.REFUSED, reason_code="RUL-01",
                gates_passed=gates_passed, gates_failed=gates_failed,
                counterfactual=f"Reduce DSTI to <= {max_dsti * 100:.0f}%",
                explanation=f"DSTI ratio {proposal.dsti_ratio * 100:.0f}% exceeds policy limit of {max_dsti * 100:.0f}%.",
                policy_version=pv, evaluated_at=evaluated_at, correlation_id=corr_id
            ))
        gates_passed.append("G2_RULES")

        # Gate 3: Z3 Solver (thread-safe, fail-closed, with counterfactual)
        try:
            with self._z3_lock:
                is_valid, reason = verify_constraints(
                    proposal,
                    self.rules["high_amount_threshold"],
                    self.rules["min_term_for_high_amount"],
                    self.rules.get("max_term_months", 120)
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
                explanation=f"Uncertainty upper bound ({upper_bound:.1f}%) exceeds pilot threshold (5.0%).",
                policy_version=pv, evaluated_at=evaluated_at, correlation_id=corr_id
            ))
        gates_passed.append("G4_UNCERTAINTY")

        # Gate 5: Fidelity (real validation)
        if gates_failed:
            last_failed = gates_failed[-1]
            if last_failed == "G1_SCHEMA":
                explanation = "Invalid schema: amount and DSTI must be strictly positive and finite, and at least one fact must be cited."
            elif last_failed == "G2_RULES":
                explanation = f"DSTI ratio {proposal.dsti_ratio * 100:.0f}% exceeds policy limit of {max_dsti * 100:.0f}%."
            elif last_failed == "G3_SOLVER":
                explanation = reason if 'reason' in locals() else "Violates formal constraints."
            elif last_failed == "G4_UNCERTAINTY":
                explanation = f"Uncertainty upper bound ({upper_bound:.1f}%) exceeds pilot threshold (5.0%)."
            else:
                explanation = "Unknown failure."
        else:
            explanation = "Proposal meets all schema, rule, formal, and uncertainty criteria."
        
        if gates_failed and not any(gate in explanation for gate in gates_failed):
            gates_failed.append("G5_FIDELITY")
            return self._apply_shadow(PortResult(
                outcome=OutcomeEnum.ESCALATED, reason_code="FID-01",
                gates_passed=gates_passed, gates_failed=gates_failed,
                explanation="Fidelity check failed: explanation does not reference failed gates.",
                policy_version=pv, evaluated_at=evaluated_at, correlation_id=corr_id
            ))
        
        pii_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}|\d{9,}'
        if re.search(pii_pattern, explanation):
            gates_failed.append("G5_FIDELITY")
            return self._apply_shadow(PortResult(
                outcome=OutcomeEnum.ESCALATED, reason_code="FID-02",
                gates_passed=gates_passed, gates_failed=gates_failed,
                explanation="Fidelity check failed: explanation contains potential PII.",
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
        if self.shadow_mode:
            result.shadow_outcome = result.outcome.value
            result.shadow_reason_code = result.reason_code
        return result
