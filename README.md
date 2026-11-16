# 🛡️ TrustPort

**Port: mandatory validation for AI outputs.**

[![CI](https://github.com/rafaelcontente/TrustPort/actions/workflows/ci.yml/badge.svg?branch=main&style=for-the-badge)](https://github.com/rafaelcontente/TrustPort/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-84%25-brightgreen?style=for-the-badge&logo=codecov)](https://github.com/rafaelcontente/TrustPort)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Z3 Verified](https://img.shields.io/badge/Z3-formal_verification-purple?style=for-the-badge&logo=github)](https://github.com/Z3Prover/z3)
[![Hypothesis](https://img.shields.io/badge/Hypothesis-property_testing-orange?style=for-the-badge)](https://hypothesis.readthedocs.io/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Ruff](https://img.shields.io/badge/ruff-formatted-41B883?style=for-the-badge&logo=ruff)](https://docs.astral.sh/ruff/)
[![Mypy](https://img.shields.io/badge/mypy-type_checked-2B65EC?style=for-the-badge&logo=mypy)](https://mypy-lang.org/)
[![License](https://img.shields.io/badge/license-MIT-22c55e?style=for-the-badge)](LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/rafaelcontente/TrustPort?style=for-the-badge&logo=git)](https://github.com/rafaelcontente/TrustPort/commits/main/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=for-the-badge&logo=github)](https://github.com/rafaelcontente/TrustPort/pulls)

## 🎯 The Problem

An LLM will happily approve a loan it should refuse — fluently, confidently, and without checking a single rule. In credit and compliance, that confidence is a liability, not a feature. TrustPort answers one question: *can this AI proposal provably reach a human — or must it be repaired, escalated, or refused?*

## ✅ What it solves

TrustPort replaces *trust the model* with *check the proposal*. Every AI output gets a deterministic verdict — 🟢 APPROVED, 🔵 REPAIRED, 🟠 ESCALATED or 🔴 REFUSED — plus a machine-readable reason code. Refusals ship with a counterfactual the customer can act on ("reduce DSTI to ≤ 40%"), never a bare no. Measured today: **100/100 invalid proposals blocked, zero silent approvals, every refusal explained**. The agent proposes; the Port decides.

## 🚫 What this is NOT

Not a chatbot. Not a generic input validator. It is the gate between an LLM and the real world: every proposal is checked, every refusal is explained, every outcome is typed.

## ⚡ Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
make test
```

Three commands, under five minutes — 54 regression tests prove the gate holds.

## 🏗️ Architecture

```mermaid
graph TD
    A[AgentProposal] --> G1{G1 Schema}
    G1 -->|pass| G2{G2 Rules}
    G2 -->|pass| G3{G3 Z3 Solver}
    G3 -->|pass| G4{G4 Conformal}
    G4 -->|pass| G5{G5 Fidelity}
    G5 -->|pass| OK((APPROVED))
    G1 -->|fail| REP[REPAIRED]
    G2 -->|fail| REF[REFUSED]
    G3 -->|fail| REF
    G4 -->|fail| ESC[ESCALATED]
    style OK fill:#22c55e,stroke:#16a34a,color:#fff
    style REP fill:#3b82f6,stroke:#2563eb,color:#fff
    style REF fill:#ef4444,stroke:#dc2626,color:#fff
    style ESC fill:#f59e0b,stroke:#d97706,color:#fff
```

One proposal, five serial gates, zero silent passes. The first gate to say no stops the run and returns a typed `PortResult`: outcome, reason code, counterfactual. 🟢 green is safe to execute, 🔵 blue goes back to the agent for repair, 🟠 amber waits for a human, 🔴 red ends with an explanation the customer can act on. Deep dive in [ARCHITECTURE.md](docs/ARCHITECTURE.md).

## 📊 Evaluation

Baseline: synthetic credit pilot — 54 regression tests, all green. Only measured numbers appear here; no aspirational metrics.

- 🚫 **100/100** invalid proposals blocked, zero slipped through as APPROVED (REG-001).
- 💬 **100%** of refusals ship with an actionable counterfactual, not just a no (REG-003, REG-007).
- 🎯 **Conformal coverage ~90%** on held-out test set (REG-006).
- ⚡ **<5ms p50 latency**, >100 req/s throughput (REG-011).

Full tables and methodology live in [EVALUATION.md](docs/EVALUATION.md).

## ⚠️ Limitations

Honesty over hype — what is done and what is not:

- ✅ **G3 (Z3 Solver):** Enforces formal constraints (e.g., high amount requires long term, max term bounds). Proven in REG-005, REG-018.
- ✅ **G4 (Conformal):** Split Conformal Prediction engine with drift detection and segmented coverage validation (REG-006, REG-022). Live routing still uses heuristic proxy pending trained base model.
- ✅ **Audit:** Immutable logging with chained SHA-256 hashes (REG-023).
- 📉 Calibration runs on synthetic data, not production credit portfolios.
- 🗂️ TrustPort validates; immutable persistence belongs to TrustAudit deployment layer.

Full context and evidence in [LIMITATIONS.md](docs/LIMITATIONS.md).

## 🧩 Composition

TrustPort is one gate in a larger trust layer. It speaks Pydantic contracts — `AgentProposal`, `PortResult`, `OutcomeEnum` — with **TrustAgent**, which proposes but never executes, and **TrustAudit**, which records every outcome in an append-only hash chain. Cited facts from **TrustKnowledge** feed the Gate 4 uncertainty penalty: fewer sources, wider bounds, faster escalation.

## 📚 Documentation

- 🏗️ [ARCHITECTURE.md](docs/ARCHITECTURE.md) — gates, contracts, fail-fast design
- 📊 [EVALUATION.md](docs/EVALUATION.md) — benchmarks and methodology
- ⚠️ [LIMITATIONS.md](docs/LIMITATIONS.md) — what is proven and what is not
- 🗺️ [ROADMAP.md](docs/ROADMAP.md) — SHAP explanations, conditional conformal
- 🔌 [docs/api.md](docs/api.md) — contract reference

## 📄 License

MIT — see [LICENSE](LICENSE).

## HTTP API

TrustPort exposes a REST API with automatic OpenAPI spec.

```bash
uvicorn trust_net_port.api:app --reload   # start server
open http://localhost:8000/docs           # interactive docs
```

Endpoints: POST /validate, GET /health, GET /stats. Every decision is logged to the SQLite audit store with chained hashes.
