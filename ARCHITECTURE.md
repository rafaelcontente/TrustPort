# 🏗️ Architecture

TrustPort runs every `AgentProposal` through five serial gates. Fail-fast: the first rejection stops the run. No gate is skipped, no output bypasses the pipeline.

## Gates and status

| Gate | Check | On failure | Status |
|------|-------|-----------|--------|
| G1 Schema | positive amount, valid DSTI, >=1 cited fact | REPAIRED (SCH-01) | ✅ implemented |
| G2 Rules | DSTI <= 40% policy limit | REFUSED (RUL-01) + counterfactual | ✅ policy-as-code |
| G3 Solver | formal constraint satisfaction | REFUSED (SMT-01) | 🧪 placeholder — Z3 next |
| G4 Uncertainty | PD upper bound <= 5.0% pilot threshold | ESCALATED (UNC-02) | 🧪 heuristic — split conformal next |
| G5 Explanation | reasons + counterfactual attached | — | ✅ rule-based; SHAP planned |

This table reflects the code, not the ambition.

## Contracts

Defined in `src/trust_net_port/schema/contracts.py`:

- **AgentProposal** — proposal_id, case_id, action, amount, term_months, dsti_ratio, facts_cited
- **PortResult** — outcome, reason_code, gates_passed, gates_failed, counterfactual, explanation
- **OutcomeEnum** — APPROVED / REPAIRED / ESCALATED / REFUSED

## Outcome routing

- 🔵 REPAIRED → back to TrustAgent with the error code (fixable input)
- 🔴 REFUSED → terminal; customer-facing notice with counterfactual
- 🟠 ESCALATED → human review queue (uncertainty too high)
- 🟢 APPROVED → safe to hand off; TrustAudit logs every outcome

## Design rules

1. Deterministic code decides — never an LLM.
2. Every rejection carries a reason code; no silent failures.
3. The uncertainty penalty is input-driven: fewer cited facts or DSTI near the limit widens the bound.
4. Maker-checker: the Port is the checker; it never generates proposals.
