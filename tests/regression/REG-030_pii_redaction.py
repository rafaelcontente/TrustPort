"""Tests for the Gate 0 PII Redaction module."""
from trust_net_port.pii_redactor import redact_pii, redact_proposal_pii


def test_redact_pii_email():
    assert redact_pii("Contact: user@test.com") == "Contact: [REDACTED_EMAIL]"


def test_redact_pii_phone():
    assert redact_pii("Phone: +351 912 345 678") == "Phone: [REDACTED_PHONE]"
    assert redact_pii("Phone: 912345678") == "Phone: [REDACTED_PHONE]"


def test_redact_proposal_pii():
    proposal = {
        "proposal_id": "P-123",
        "case_id": "client@email.com",
        "action": "approve",
        "amount": 10000.0,
        "term_months": 12,
        "dsti_ratio": 0.30,
        "facts_cited": ["Ligou do 912 345 678", "Rendimento estável"],
    }
    redacted = redact_proposal_pii(proposal)

    assert redacted["case_id"] == "[REDACTED_EMAIL]"
    assert redacted["proposal_id"] == "P-123"  # Unchanged, no PII
    assert redacted["facts_cited"][0] == "Ligou do [REDACTED_PHONE]"
    assert redacted["facts_cited"][1] == "Rendimento estável"  # Unchanged
