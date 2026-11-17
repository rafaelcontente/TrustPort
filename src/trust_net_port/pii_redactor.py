"""PII Redaction Module for TrustPort (Gate 0).

Ensures GDPR compliance by redacting sensitive data before processing or logging.
"""
import re

# Regex patterns for common PII
# Uses [.] instead of \. to avoid Python 3.12+ SyntaxWarning in raw strings
EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+[.][a-zA-Z]{2,}")

# Matches international and Portuguese phone numbers (e.g., +351 912 345 678, 912345678)
# Looks for an optional +, followed by digits, spaces, dashes or dots, total length 9-15 digits
PHONE_PATTERN = re.compile(r"\+?\d[\d\s\-\.]{7,15}\d")


def redact_pii(text: str) -> str:
    """Redacts PII from a given string."""
    if not isinstance(text, str):
        return str(text)
    text = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", text)
    text = PHONE_PATTERN.sub("[REDACTED_PHONE]", text)
    return text


def redact_proposal_pii(proposal_dict: dict) -> dict:
    """Redacts PII from a proposal dictionary."""
    redacted = proposal_dict.copy()

    # Redact in facts_cited
    if "facts_cited" in redacted and isinstance(redacted["facts_cited"], list):
        redacted["facts_cited"] = [redact_pii(fact) for fact in redacted["facts_cited"]]

    # Redact in case_id and proposal_id (common places for accidental PII in demos)
    if "case_id" in redacted:
        redacted["case_id"] = redact_pii(str(redacted["case_id"]))
    if "proposal_id" in redacted:
        redacted["proposal_id"] = redact_pii(str(redacted["proposal_id"]))

    return redacted
