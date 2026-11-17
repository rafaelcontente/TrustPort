# 🔌 API Reference

Contracts live in `src/trust_net_port/schema/contracts.py`. They are the boundary with TrustAgent, TrustKnowledge and TrustAudit — changing a field is a breaking change and requires a version bump.

## AgentProposal (input)

| Field | Type | Meaning |
|-------|------|---------|
| proposal_id | str | unique proposal identifier |
| case_id | str | credit case reference |
| action | str | requested action (e.g. approve) |
| amount | float | requested amount, EUR |
| term_months | int | loan term in months |
| dsti_ratio | float | debt-service-to-income, percent |
| facts_cited | list[str] | Knowledge fact ids backing the proposal |

## PortResult (output)

| Field | Type | Meaning |
|-------|------|---------|
| outcome | OutcomeEnum | APPROVED / REPAIRED / ESCALATED / REFUSED |
| reason_code | str | machine-readable cause (see below) |
| gates_passed | list[str] | e.g. G1_SCHEMA, G2_RULES |
| gates_failed | list[str] | empty on approval |
| counterfactual | str or None | actionable change suggestion |
| explanation | str or None | human-readable reason |

## Reason codes (implemented)

| Code | Outcome | Trigger |
|------|---------|---------|
| SCH-01 | REPAIRED | non-positive amount, negative DSTI, or zero cited facts |
| RUL-01 | REFUSED | DSTI above the 40% policy limit |
| UNC-02 | ESCALATED | uncertainty upper bound above the 5.0% pilot threshold |
| OK-00 | APPROVED | all gates passed |

SMT-01 (formal violation) is planned with the real Z3 gate — ROADMAP M1. It does not exist in the current code.

## Usage

```python
from trust_net_port.schema.contracts import AgentProposal
from trust_net_port.validator import PortValidator

proposal = AgentProposal(
    proposal_id="P-001",
    case_id="C-0142",
    action="approve",
    amount=40000.0,
    term_months=60,
    dsti_ratio=36.0,
    facts_cited=["F-221", "F-340", "F-500"],
)
result = PortValidator().validate(proposal)
print(result.outcome, result.reason_code)
```

Validation is deterministic and side-effect free: no I/O, no persistence, no network. The caller owns logging (TrustAudit) and execution.
