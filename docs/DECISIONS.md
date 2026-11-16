# 📜 Architectural Decision Records (ADRs)

This document records the structural decisions made in TrustPort.

## ADR-001: Maker-Checker Architecture
**Status:** Accepted
**Context:** LLMs are prone to hallucinations and rule violations.
**Decision:** TrustPort acts strictly as the "Checker". It never generates proposals. The "Maker" (TrustAgent) proposes, and the Port validates deterministically.
**Consequences:** Clear separation of concerns. The Port can be audited independently of the LLM.

## ADR-002: Fail-Closed on External Dependencies
**Status:** Accepted
**Context:** Z3 solver or Conformal engine might timeout or crash.
**Decision:** Any exception in G3 (Z3) or G4 (Conformal) immediately returns `REFUSED` (SMT-ERR) or `ESCALATED`. It never defaults to `APPROVED`.
**Consequences:** Maximum safety, potential false positives under heavy load, which is acceptable for credit/compliance.

## ADR-003: Shadow Mode is Strictly Observational
**Status:** Accepted
**Context:** Need to test new policies/models without impacting production.
**Decision:** Shadow mode records the hypothetical outcome in `shadow_outcome` and `shadow_reason_code`, but **never** alters the primary `outcome`.
**Consequences:** Safe A/B testing. Audit logs reflect the actual decision made, with shadow data available for analysis.

## ADR-004: Marginal Conformal over Conditional (for v1.0)
**Status:** Accepted
**Context:** Conditional (Mondrian) conformal provides better tail coverage but requires complex segment calibration.
**Decision:** Use Marginal Split Conformal for v1.0, but explicitly document and test the degradation in heteroscedastic tails (~70% coverage for high-risk segments).
**Consequences:** Simpler implementation, but requires human escalation (G4) for high-uncertainty edge cases.

## ADR-005: SQLite WAL for Local Audit Logging
**Status:** Accepted
**Context:** Audit logs must be durable and tamper-evident.
**Decision:** Use SQLite in WAL (Write-Ahead Logging) mode with chained SHA-256 hashes. 
**Consequences:** Provides crash recovery and basic tamper detection. Production deployments should wrap this in an append-only database or S3 with object lock.
