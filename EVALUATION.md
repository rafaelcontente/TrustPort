# 📊 Evaluation

Only numbers produced by the regression suite appear here. Each row states whether it is a real measurement or a declared placeholder.

## Baseline

- Dataset: synthetic credit pilot (no production data)
- Suite: 9 tests, REG-001 to REG-004, all green
- Environment: local Python 3.15; CI matrix 3.10 / 3.11 / 3.12
- Deterministic: no LLM in the loop, same input always yields the same outcome

## Results

| Metric | Result | Source | Kind |
|--------|--------|--------|------|
| Invalid proposals blocked | 100/100, zero APPROVED | REG-001 | ✅ measured |
| Refusals with actionable counterfactual | 2/2 (100%) | REG-003 | ✅ measured |
| ECE on calibration fixture | 0.0 (< 0.05 threshold) | REG-002 | ✅ measured, synthetic fixture |
| Conformal coverage vs 90% target | 0.915 fixture value | REG-002 | ⚠️ placeholder, not measured |
| Uncertainty routing (quality-driven) | high-quality APPROVED, low-quality ESCALATED | REG-004 | ✅ measured |

The ECE fixture is perfectly calibrated by construction — it proves the metric plumbing, not model quality. The coverage row is a hardcoded stub until split-conformal calibration lands (see ROADMAP).

## Methodology

Run `pytest tests/regression/port/ -v`. REG-001 generates 100 invalid proposals (50 negative amounts, 50 DSTI violations) and asserts zero approvals. REG-003 checks every refusal carries a concrete reason and a counterfactual. REG-004 proves the uncertainty bound is input-driven, not a constant.

## Not measured yet

- Empirical conformal coverage on a held-out calibration set
- ECE on production-like, imperfectly calibrated predictions
- Gate latency and throughput under load
