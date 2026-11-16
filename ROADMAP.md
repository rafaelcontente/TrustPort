# 🗺️ Roadmap

Ordered by risk reduction, not by feature count. Each milestone closes a numbered limitation in LIMITATIONS.md and is only done when its acceptance test is green.

## M1 — Real formal verification (closes L1)

- 🧮 Reintroduce Z3 in G3: amount, DSTI and facts constraints first.
- One REG test per constraint: valid proposals satisfiable, each violation returns unsat with SMT-01.
- Acceptance: G3 rejects what G2 misses; solver tests green in CI.

## M2 — Real conformal prediction (closes L2, L3)

- 📐 Split-conformal calibration on a held-out set; quantile from residuals, not a constant.
- Replace the 0.915 coverage stub with measured empirical coverage; target 90% within ±2pp.
- ECE evaluated on imperfect predictions, not perfect fixtures.
- Acceptance: REG-002 measures instead of asserting fixtures.

## M3 — Verified counterfactuals (closes L4)

- 🔁 Mutate-and-revalidate: apply the suggested change, re-run the pipeline, assert the outcome flips.
- Acceptance: 100% of refusal counterfactuals provably change the result.

## M4 — Policy-as-code (closes L5)

- 📜 Versioned, cited rules: every threshold traceable to a source, version and effective date.
- Acceptance: changing a rule requires a version bump plus a test.

## M5 — Explainability and deployment layer

- 🔭 SHAP attributions in G5 once a real model exists; shadow mode and drift alarms before production traffic; every PortResult appended to the TrustAudit hash chain.

## Not planned

- Generic validation, proposal generation, persistence — out of scope by design (see LIMITATIONS.md).
