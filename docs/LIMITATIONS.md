# ⚠️ Limitations

What is proven, what is not, and why. Each item lists the impact and the evidence. This file is updated whenever a limitation is closed or opened — never silently.

## Proven and Active

### G1: Schema & Policy Limits
**What it validates:** amount in (0, max_amount], DSTI > 0 and finite, term >= min_term, facts count in [1, max_facts].
**How it fails:** REPAIRED (SCH-01) with explanation of which limit was violated.
**Evidence:** REG-013, REG-021, REG-001.

### G2: Rules (DSTI Policy)
**What it validates:** DSTI ratio <= policy limit (default 40%).
**How it fails:** REFUSED (RUL-01) with counterfactual "Reduce DSTI to <= X%".
**Evidence:** REG-001, REG-003, REG-018.

### G3: Z3 Solver (Formal Constraints)
**What it validates:** High amount (> 50k) requires long term (>= 36 months). Term must not exceed max (120 months).
**How it fails:** REFUSED (SMT-01) with counterfactual.
**Evidence:** REG-005, REG-018, REG-014, REG-017.
**Known limitation:** Z3 solver is not thread-safe; protected by threading.Lock().

### G4: Uncertainty (Split Conformal + Heuristic)
**What it validates:** Conformal engine (REG-006, REG-022) + Heuristic proxy (live routing).
**Why heuristic in live traffic:** Conformal requires a trained base model.
**Evidence:** REG-006, REG-022, REG-002.
**Known limitation:** Marginal conformal degrades in heteroscedastic tails (~70% for X > 1.0).

### G5: Fidelity
**What it validates:** Explanation references failed gates, no PII, deterministic.
**How it fails:** ESCALATED (FID-01, FID-02).
**Evidence:** REG-020.

### Audit & Observability
**What it provides:** correlation_id (UUID), evaluated_at, policy_version, shadow fields, chained SHA-256 hashes.
**Evidence:** REG-009, REG-012, REG-015, REG-023.

## Not Proven Yet
1. Production calibration (synthetic data only).
2. Conditional conformal coverage (marginal degrades in tails).
3. Semantic counterfactual validation (existence vs correctness).

## Out of Scope by Design
- No persistence (TrustAudit owns storage).
- No generation (Maker-Checker).
- Credit-only schema.
- No LLM in the loop.
