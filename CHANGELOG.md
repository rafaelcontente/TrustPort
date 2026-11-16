# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-05-XX (Current)

### Added
- **5-Gate Validation Pipeline:** Schema (G1), Rules (G2), Z3 Formal Verification (G3), Conformal Uncertainty (G4), Fidelity (G5).
- **HTTP API:** FastAPI wrapper with automatic OpenAPI spec (`/docs`).
- **TrustAudit:** SQLite WAL append-only store with SHA-256 chained hashes for tamper detection.
- **Shadow Mode:** Strictly observational mode for safe A/B testing of policies.
- **Property-Based Testing:** Hypothesis suite proving core invariants (determinism, fail-closed, edge cases).

### Changed
- Upgraded documentation to include ADRs, Risk Model, and honest Coverage metrics (84%).
- CI now gates on `ruff`, `mypy`, `pytest`, and `coverage >= 80%` across Python 3.10-3.12.

### Fixed
- Resolved Z3 thread-safety issues via explicit locking.
- Fixed G5 fidelity checks to prevent PII leakage in explanations.
