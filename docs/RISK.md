# ⚠️ Risk & Threat Model

TrustPort is designed to mitigate specific risks in AI-mediated decision-making.

## 1. Adversarial Prompt Injection
- **Threat:** Malicious input tries to bypass rules or inject PII.
- **Mitigation:** G1 strictly validates schema (no arbitrary text fields for core logic). G5 scans explanations for PII patterns before returning.

## 2. Solver Denial of Service (DoS)
- **Threat:** Complex Z3 constraints cause the solver to hang, blocking the pipeline.
- **Mitigation:** Z3 calls are protected by a `threading.Lock` (preventing thread explosion) and wrapped in a try/except that fails closed (`SMT-ERR`) on any exception or timeout.

## 3. Model Drift / Miscalibration
- **Threat:** The underlying AI model's uncertainty estimates become unreliable over time.
- **Mitigation:** G4 includes a `check_drift()` method that compares current residuals against the calibration baseline. High uncertainty triggers `ESCALATED` (human review), never `APApproved`.

## 4. Audit Log Tampering
- **Threat:** An insider alters a historical decision in the database.
- **Mitigation:** Each log entry contains the SHA-256 hash of the previous entry. The `verify_chain()` method will return `False` if any historical record is altered.

## 5. Silent Failures
- **Threat:** A bug causes invalid proposals to slip through as `APPROVED`.
- **Mitigation:** 71 automated tests, including Hypothesis property-based testing, explicitly assert that invalid inputs *never* result in `APPROVED`. CI blocks any coverage drop below 80%.
