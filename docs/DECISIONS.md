# 📝 Architectural Decision Records (ADRs)

Significant technical choices, why they were made, and their trade-offs.

## ADR-001: Strict Pydantic Contracts for Module Boundaries

- **Status:** Accepted
- **Context:** TrustPort must communicate with TrustAgent and TrustAudit without tight coupling.
- **Decision:** All inputs (`AgentProposal`) and outputs (`PortResult`) are strictly typed Pydantic models.
- **Consequences:** Breaking changes require a version bump. Validation is automatic and deterministic. No implicit type coercion from LLM outputs.

## ADR-002: Fail-Fast Serial Gates

- **Status:** Accepted
- **Context:** Running all 5 gates on an invalid proposal wastes compute and obscures the root cause.
- **Decision:** The pipeline stops at the first failing gate. The `PortResult` contains only the gates evaluated up to that point.
- **Consequences:** Faster rejection. Callers must fix G1 issues before G2 rules are even evaluated. Counterfactuals are tied to the specific failing gate.

## ADR-003: Heuristic Uncertainty (G4) before Full Conformal Prediction

- **Status:** Accepted (Temporary)
- **Context:** Real split-conformal prediction requires a trained base model and a held-out calibration set, which are not yet available in the synthetic pilot.
- **Decision:** G4 currently uses a deterministic heuristic (base + fact penalty + DSTI penalty) to simulate uncertainty routing.
- **Consequences:** The 5.0% threshold is arbitrary. Coverage is not statistically guaranteed. This is explicitly documented in `docs/LIMITATIONS.md` and slated for replacement in ROADMAP M2.

## ADR-004: No Persistence in TrustPort

- **Status:** Accepted
- **Context:** Auditability is a core manifesto requirement, but mixing validation logic with storage creates tight coupling and statefulness.
- **Decision:** TrustPort is purely functional and stateless. It returns `PortResult` objects. The caller (or a sidecar) is responsible for appending the result to the TrustAudit hash chain.
- **Consequences:** TrustPort can be scaled horizontally without state synchronization. Auditability is guaranteed by the external contract, not internal implementation.
