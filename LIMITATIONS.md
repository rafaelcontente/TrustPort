# ⚠️ Limitations

What is not proven yet, stated plainly. Each item lists the impact and the mitigation path. This file is updated whenever a limitation is closed — never silently.

## Not proven yet

1. **G3 is a placeholder.** The solver gate currently passes every schema-valid proposal; it proves nothing formally. A Z3 draft exists in git history but was reverted before it was ever tested. *Impact:* formal violations are only caught if G2 also catches them. *Mitigation:* reintroduce Z3 with REG tests per constraint (ROADMAP M1).
2. **G4 is a heuristic, not conformal prediction.** The bound is base + fact penalty + DSTI penalty. No calibration set, no quantile, no coverage guarantee. The 0.915 coverage figure in REG-002 is a declared stub. *Impact:* the 90% coverage claim is unproven. *Mitigation:* split-conformal calibration on a held-out set, empirical coverage test (ROADMAP M2).
3. **Calibration fixture is perfect by construction.** ECE 0.0 proves the metric plumbing, not model quality. *Impact:* no evidence the metric catches miscalibration in the wild. *Mitigation:* evaluate on imperfect synthetic predictions, then real data.
4. **Counterfactuals are not re-validated.** REG-003 checks presence and wording, not that applying the counterfactual flips the outcome. *Impact:* an explanation could be actionable in text but wrong in effect. *Mitigation:* mutate-and-revalidate test through the full pipeline (ROADMAP M3).
5. **Thresholds are pilot constants.** DSTI 40% and PD 5.0% are declared, not derived from a regulatory source. *Impact:* policy correctness is assumed, not audited. *Mitigation:* policy-as-code with versioned, cited rules.

## Out of scope by design

- No persistence: outcomes are returned, not stored. TrustAudit owns the hash chain.
- No generation: the Port never proposes; Maker-Checker is structural.
- Credit-only schema: this is not a generic validator.
- No drift monitoring or shadow mode yet — both belong to the deployment layer, tracked in ROADMAP.
