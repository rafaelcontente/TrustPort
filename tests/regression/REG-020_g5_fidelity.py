from trust_net_port.schema.contracts import AgentProposal, OutcomeEnum
from trust_net_port.validator import PortValidator


def test_g5_explanation_references_failed_gates():
    """Explicação deve mencionar os gates que falharam."""
    validator = PortValidator()

    # Proposta que falha no G2
    proposal = AgentProposal(
        proposal_id="P-G5-01",
        case_id="C-G5-01",
        action="approve",
        amount=10000.0,
        term_months=12,
        dsti_ratio=0.50,
        facts_cited=["F-1", "F-2", "F-3"],
    )
    result = validator.validate(proposal)

    assert result.outcome == OutcomeEnum.REFUSED
    assert "G2_RULES" in result.gates_failed
    assert "G2_RULES" in result.explanation or "DSTI" in result.explanation


def test_g5_no_pii_in_explanation():
    """Explicação não deve conter PII (emails, telefones)."""
    validator = PortValidator()

    # Proposta normal (não deve ter PII)
    proposal = AgentProposal(
        proposal_id="P-G5-02",
        case_id="C-G5-02",
        action="approve",
        amount=10000.0,
        term_months=12,
        dsti_ratio=0.30,
        facts_cited=["F-1", "F-2", "F-3"],
    )
    result = validator.validate(proposal)

    # Verificar que não há padrão de email ou telefone
    import re

    pii_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}|\d{9,}"
    assert not re.search(pii_pattern, result.explanation)


def test_g5_deterministic_explanation():
    """Mesma entrada deve produzir mesma explicação."""
    validator = PortValidator()
    proposal = AgentProposal(
        proposal_id="P-G5-03",
        case_id="C-G5-03",
        action="approve",
        amount=10000.0,
        term_months=12,
        dsti_ratio=0.50,
        facts_cited=["F-1", "F-2", "F-3"],
    )

    r1 = validator.validate(proposal)
    r2 = validator.validate(proposal)

    assert r1.explanation == r2.explanation
