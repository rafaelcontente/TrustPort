import random

from trust_net_port.schema.contracts import AgentProposal, OutcomeEnum
from trust_net_port.validator import PortValidator


def generate_invalid_proposal():
    """Gera uma proposta inválida aleatória."""
    return AgentProposal(
        proposal_id=f"PROP-{random.randint(1, 100000)}",
        case_id=f"C-{random.randint(1, 100000)}",
        action="approve",
        amount=random.choice([-1000, 0, 50000]),  # Inválido
        term_months=random.choice([-1, 0, 12]),
        dsti_ratio=random.uniform(-10, 100),
        facts_cited=[] if random.random() > 0.5 else ["F-1"],
    )


def test_property_no_invalid_proposal_is_approved():
    """Propriedade: Nenhuma proposta inválida é aprovada."""
    validator = PortValidator()
    for _ in range(1000):
        p = generate_invalid_proposal()
        result = validator.validate(p)
        assert result.outcome != OutcomeEnum.APPROVED, f"Proposta inválida aprovada: {p}"


def test_property_every_refusal_has_reason_and_counterfactual():
    """Propriedade: Toda a recusa tem motivo e contrafactual."""
    validator = PortValidator()
    # Proposta que falha no G2 (DSTI alto)
    p = AgentProposal(
        proposal_id="P-PROP-01",
        case_id="C-PROP-01",
        action="approve",
        amount=10000.0,
        term_months=12,
        dsti_ratio=0.50,
        facts_cited=["F-1", "F-2", "F-3"],
    )
    result = validator.validate(p)
    if result.outcome == OutcomeEnum.REFUSED:
        assert result.reason_code is not None
        assert result.counterfactual is not None


def test_property_monotonic_risk():
    """Propriedade: Pior DSTI nunca reduz o nível de cautela."""
    validator = PortValidator()
    p1 = AgentProposal(
        proposal_id="P-MON-01",
        case_id="C-MON-01",
        action="approve",
        amount=10000.0,
        term_months=12,
        dsti_ratio=0.30,
        facts_cited=["F-1", "F-2", "F-3"],
    )
    p2 = AgentProposal(
        proposal_id="P-MON-02",
        case_id="C-MON-01",
        action="approve",
        amount=10000.0,
        term_months=12,
        dsti_ratio=0.45,
        facts_cited=["F-1", "F-2", "F-3"],
    )
    r1 = validator.validate(p1)
    r2 = validator.validate(p2)
    # Se p1 foi recusado/escalado, p2 (pior) também deve ser.
    if r1.outcome in [OutcomeEnum.REFUSED, OutcomeEnum.ESCALATED]:
        assert r2.outcome in [OutcomeEnum.REFUSED, OutcomeEnum.ESCALATED]
