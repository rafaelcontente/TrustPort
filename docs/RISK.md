# 🛡️ Risk & Threat Model

How TrustPort handles failure, abuse, and edge cases. Based on STRIDE principles applied to the validation pipeline.

## Threat Model (STRIDE)

| Threat | Vector | Mitigation in TrustPort |
|--------|--------|-------------------------|
| **Spoofing** | Malicious agent impersonating a valid user/case | G1 Schema enforces strict `case_id` and `proposal_id` formats. TrustAgent handles auth (OIDC/mTLS) before reaching the Port. |
| **Tampering** | Altered proposal payload in transit | Immutable `PortResult` generation. Any downstream mutation breaks the TrustAudit hash chain. |
| **Repudiation** | Agent claims "the Port approved this" | Every outcome is logged by TrustAudit with a cryptographic trace. The Port never approves silently. |
| **Information Disclosure** | Leaking internal rules or thresholds via error messages | Error messages are generic (`SCH-01`, `RUL-01`). Counterfactuals are actionable but do not reveal the exact mathematical boundary or internal weights. |
| **Denial of Service** | Flooding the Port with complex proposals | Stateless design allows horizontal scaling. G1 fail-fast drops invalid payloads before expensive G3/G4 compute. |
| **Elevation of Privilege** | Prompt injection forcing an `APPROVED` outcome | The Port is deterministic code, not an LLM. Prompt injections in `facts_cited` are treated as opaque strings and penalized in G4 uncertainty, never executed as commands. |

## Failure Modes

1. **G3/G4 Placeholder Failure**: Currently, G3 passes all schema-valid proposals, and G4 uses a heuristic. *Impact:* False negatives on complex constraint violations. *Mitigation:* Explicitly documented in LIMITATIONS.md; ROADMAP M1/M2 replaces these with Z3 and conformal prediction.
2. **Dependency Outage**: If `pydantic` or `numpy` fail to load, the Port crashes. *Impact:* Total service unavailability (fail-closed). *Mitigation:* CI tests on multiple Python versions; containerized deployment ensures pinned, verified dependencies.
3. **Counterfactual Hallucination**: The generated counterfactual might be mathematically insufficient to flip the outcome. *Impact:* User frustration. *Mitigation:* ROADMAP M3 introduces mutate-and-revalidate tests to prove counterfactuals actually work.

## Security Posture

- **No Execution**: The Port evaluates; it never executes actions (no DB writes, no API calls to external systems).
- **No State**: No session data or caching that could be poisoned.
- **Fail-Closed**: Any unhandled exception or missing field results in `REPAIRED` or `REFUSED`, never `APPROVED`.
