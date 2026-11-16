# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Real unit tests for `ConformalUncertaintyEstimator` (base + penalties).
- Real integration tests for the 5-gate pipeline (fail-fast validation).
- `docs/ARCHITECTURE.md`, `docs/EVALUATION.md`, `docs/LIMITATIONS.md`, `docs/ROADMAP.md`.
- `docs/api.md` with explicit contract definitions.

### Changed
- Reorganized test structure: flattened `tests/regression/`, added `tests/unit/` and `tests/integration/`.
- Updated `pyproject.toml` to discover both `test_*.py` and `REG-*.py` files.
- README restructured to strictly follow the mandated senior template (Problem -> What it solves -> What it is NOT).

### Fixed
- Removed nested `TrustPort/TrustPort` directory anomaly; project is now correctly rooted.
- Corrected README links to point to the new `docs/` directory.

## [0.1.0] - 2026-11-16

### Added
- Initial standalone repository extraction from the TrustNet monorepo.
- 5-gate validation pipeline (Schema, Rules, Solver placeholder, Uncertainty heuristic, Explanation).
- 9 baseline regression tests (REG-001 to REG-004).
- MIT License, `.gitignore`, and GitHub Actions CI workflow (Python 3.10/3.11/3.12).
