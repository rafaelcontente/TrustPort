# 📊 Evaluation

Only numbers produced by the regression suite appear here.

## Baseline
- **Suite:** 54 tests (REG-001 to REG-023), all green.
- **Deterministic:** No LLM in the loop.

## Results
| Metric | Result | Test |
|--------|--------|------|
| Invalid proposals blocked | 100/100, zero APPROVED | REG-001 |
| Refusals with counterfactual | 100% | REG-003, REG-007 |
| Conformal coverage | ~90% marginal, ~70% tail | REG-006, REG-022 |
| Z3 catches G2 blindspots | Yes | REG-005 |
| Fail-closed (Z3 crash) | SMT-ERR (REFUSED) | REG-014 |
| Audit hash chain | Tampering detected | REG-023 |
| Latency p99 | < 100 ms | REG-011 |

## Methodology
Run ```bash
make test
```
Expected: 54 passed.
