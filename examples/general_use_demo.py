"""
TrustPort: General Use Demo
============================
This script demonstrates how TrustPort can be applied to ANY domain,
not just credit. It uses two scenarios:

1. REAL ESTATE (with Open Source Data):
   - Dataset: California Housing (built-in to sklearn, 100% open source)
   - Task: Validate AI predictions of house prices.
   - Shows: Full pipeline with Conformal Uncertainty on real data.

2. GENERIC (No Data):
   - Task: Validate any AI output (e.g., medical, legal, text).
   - Shows: How to use TrustPort with a generic JSON schema.

Run this script to see TrustPort in action for any domain.
"""

import numpy as np
from pydantic import BaseModel, Field
from sklearn.datasets import fetch_california_housing
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split

from trust_net_port.audit.store import AuditStore
from trust_net_port.schema.contracts import OutcomeEnum, PortResult

# Import TrustPort components
from trust_net_port.uncertainty.conformal import SplitConformalPredictor

# ============================================================================
# SCENARIO 1: REAL ESTATE (with Open Source Data)
# ============================================================================

print("=" * 80)
print("SCENARIO 1: REAL ESTATE PRICING (California Housing Dataset)")
print("=" * 80)

# 1. Load Open Source Data (built-in, no download needed)
print("\n[1/5] Loading California Housing dataset (open source, built-in)...")
data = fetch_california_housing()
X, y = data.data, data.target

# Split: 60% train, 20% calibrate, 20% test
X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.4, random_state=42)
X_cal, X_test, y_cal, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42)
print(f"      Train: {len(X_train)}, Cal: {len(X_cal)}, Test: {len(X_test)}")

# 2. Train Model & Calibrate Conformal Predictor
print("[2/5] Training Ridge model and calibrating Split Conformal Predictor...")
base_model = Ridge(alpha=1.0)
base_model.fit(X_train, y_train)

conformal = SplitConformalPredictor(base_model=base_model, alpha=0.10)
conformal.calibrate(X_cal, y_cal)
print("      Conformal Predictor ready (90% coverage guarantee).")


# 3. Define Domain-Specific Schema
class PropertyProposal(BaseModel):
    """AI proposal for a house price prediction."""

    property_id: str
    ai_predicted_price: float = Field(..., gt=0, description="Must be positive")
    square_meters: float = Field(..., gt=0, description="Must be positive")
    features: list[float] = Field(..., min_items=8, max_items=8, description="8 California Housing features")


# 4. Define Domain-Specific Validator
class PropertyValidator:
    def __init__(self, conformal_predictor: SplitConformalPredictor):
        self.conformal = conformal_predictor
        self.audit = AuditStore(db_path="property_audit.db", code_version="1.0.0")
        self.max_price_per_sqm = 15000.0  # Policy rule

    def validate(self, proposal: PropertyProposal) -> PortResult:
        gates_passed, gates_failed = [], []

        # G1: Schema (already validated by Pydantic)
        gates_passed.append("G1_SCHEMA")

        # G2: Business Rules (Price per sqm limit)
        price_per_sqm = proposal.ai_predicted_price / proposal.square_meters
        if price_per_sqm > self.max_price_per_sqm:
            gates_failed.append("G2_RULES")
            return self._result(
                OutcomeEnum.REFUSED,
                "RUL-01",
                gates_passed,
                gates_failed,
                f"Price per sqm ({price_per_sqm:.0f}) exceeds limit ({self.max_price_per_sqm})",
            )
        gates_passed.append("G2_RULES")

        # G4: Conformal Uncertainty (Is the prediction within bounds?)
        features_array = np.array([proposal.features])
        lower, _pred, upper = self.conformal.predict_interval(features_array)
        if proposal.ai_predicted_price < lower[0] or proposal.ai_predicted_price > upper[0]:
            gates_failed.append("G4_UNCERTAINTY")
            return self._result(
                OutcomeEnum.ESCALATED, "UNC-02", gates_passed, gates_failed, f"Prediction outside 90% CI [{lower[0]:.0f}, {upper[0]:.0f}]"
            )
        gates_passed.append("G4_UNCERTAINTY")

        # All gates passed
        return self._result(OutcomeEnum.APPROVED, "OK-00", gates_passed, gates_failed, "Valid prediction")

    def _result(self, outcome, reason, passed, failed, explanation, proposal_id="unknown"):
        result = PortResult(
            outcome=outcome,
            reason_code=reason,
            gates_passed=passed,
            gates_failed=failed,
            explanation=explanation,
            policy_version="1.0",
            evaluated_at="2024-01-01T00:00:00Z",
            correlation_id="demo-prop-01",
        )
        self.audit.log(result)
        return result


# 5. Run Scenarios
print("[3/5] Running validation scenarios...")
validator = PropertyValidator(conformal)

# Scenario 1A: Valid prediction
print("\n[Scenario 1A] Valid prediction (within rules and CI)...")
valid_proposal = PropertyProposal(
    property_id="PROP-001",
    ai_predicted_price=2.5,  # Median price is ~2.0
    square_meters=100,
    features=X_test[0].tolist(),
)
result = validator.validate(valid_proposal)
print(f"      Outcome: {result.outcome.value} | Reason: {result.reason_code}")

# Scenario 1B: Rule violation (price per sqm too high)
print("[Scenario 1B] Rule violation (price per sqm > 15,000)...")
invalid_proposal = PropertyProposal(
    property_id="PROP-002",
    ai_predicted_price=2000000.0,  # Absurdly high
    square_meters=100,
    features=X_test[0].tolist(),
)
result = validator.validate(invalid_proposal)
print(f"      Outcome: {result.outcome.value} | Reason: {result.reason_code}")

# Scenario 1C: Uncertainty violation (prediction outside CI)
print("[Scenario 1C] Uncertainty violation (prediction outside 90% CI)...")
uncertain_proposal = PropertyProposal(
    property_id="PROP-003",
    ai_predicted_price=0.1,  # Too low for this feature set
    square_meters=100,
    features=X_test[0].tolist(),
)
result = validator.validate(uncertain_proposal)
print(f"      Outcome: {result.outcome.value} | Reason: {result.reason_code}")


# ============================================================================
# SCENARIO 2: GENERIC (No Data, Any Domain)
# ============================================================================

print("\n" + "=" * 80)
print("SCENARIO 2: GENERIC VALIDATION (No Data, Any Domain)")
print("=" * 80)


# 1. Define Generic Schema
class GenericProposal(BaseModel):
    """Generic AI proposal for any domain."""

    proposal_id: str
    action: str = Field(..., description="approve, refuse, escalate")
    payload: dict = Field(..., description="Domain-specific data as JSON")
    facts_cited: list[str] = Field(..., min_items=1, description="Sources for the decision")


# 2. Define Generic Validator
class GenericValidator:
    def __init__(self):
        self.audit = AuditStore(db_path="generic_audit.db", code_version="1.0.0")

    def validate(self, proposal: GenericProposal) -> PortResult:
        gates_passed, gates_failed = [], []

        # G1: Schema (validated by Pydantic)
        gates_passed.append("G1_SCHEMA")

        # G2: Generic Rules (e.g., action must be valid, payload must have keys)
        if proposal.action not in ["approve", "refuse", "escalate"]:
            gates_failed.append("G2_RULES")
            return self._result(OutcomeEnum.REFUSED, "RUL-01", gates_passed, gates_failed, "Invalid action", proposal.proposal_id)
        if not proposal.payload:
            gates_failed.append("G2_RULES")
            return self._result(OutcomeEnum.REFUSED, "RUL-02", gates_passed, gates_failed, "Empty payload", proposal.proposal_id)
        gates_passed.append("G2_RULES")

        # G5: Fidelity (facts must be cited)
        if len(proposal.facts_cited) == 0:
            gates_failed.append("G5_FIDELITY")
            return self._result(OutcomeEnum.ESCALATED, "FID-01", gates_passed, gates_failed, "No facts cited", proposal.proposal_id)
        gates_passed.append("G5_FIDELITY")

        return self._result(OutcomeEnum.APPROVED, "OK-00", gates_passed, gates_failed, "Valid generic proposal", proposal.proposal_id)

    def _result(self, outcome, reason, passed, failed, explanation, proposal_id="unknown"):
        result = PortResult(
            outcome=outcome,
            reason_code=reason,
            gates_passed=passed,
            gates_failed=failed,
            explanation=explanation,
            policy_version="1.0",
            evaluated_at="2024-01-01T00:00:00Z",
            correlation_id=proposal_id,
        )
        self.audit.log(result)
        return result


# 3. Run Generic Scenarios
print("\n[4/5] Running generic validation scenarios...")
gen_validator = GenericValidator()

# Scenario 2A: Valid generic proposal
print("\n[Scenario 2A] Valid generic proposal...")
valid_generic = GenericProposal(
    proposal_id="GEN-001", action="approve", payload={"diagnosis": "flu", "confidence": 0.95}, facts_cited=["medical-guideline-2024"]
)
result = gen_validator.validate(valid_generic)
print(f"      Outcome: {result.outcome.value} | Reason: {result.reason_code}")

# Scenario 2B: Invalid action
print("[Scenario 2B] Invalid action...")
invalid_generic = GenericProposal(
    proposal_id="GEN-002",
    action="maybe",  # Invalid
    payload={"diagnosis": "flu"},
    facts_cited=["medical-guideline-2024"],
)
result = gen_validator.validate(invalid_generic)
print(f"      Outcome: {result.outcome.value} | Reason: {result.reason_code}")


print("\n" + "=" * 80)
print("[5/5] Demo complete. Check property_audit.db and generic_audit.db for logs.")
print("=" * 80)
