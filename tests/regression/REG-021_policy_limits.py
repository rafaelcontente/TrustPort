from trust_net_port.schema.contracts import AgentProposal, OutcomeEnum
from trust_net_port.validator import PortValidator


def test_g1_policy_limits_amount():
    validator = PortValidator()
    # Montante acima do máximo (1M)
    p = AgentProposal(proposal_id="P-LIM-01", case_id="C-LIM-01", action="approve",
                      amount=2000000.0, term_months=12, dsti_ratio=30.0, facts_cited=["F1"])
    assert validator.validate(p).outcome == OutcomeEnum.REPAIRED

def test_g1_policy_limits_term():
    validator = PortValidator()
    # Prazo abaixo do mínimo (6 meses)
    p = AgentProposal(proposal_id="P-LIM-02", case_id="C-LIM-02", action="approve",
                      amount=10000.0, term_months=3, dsti_ratio=30.0, facts_cited=["F1", "F2", "F3"])
    assert validator.validate(p).outcome == OutcomeEnum.REPAIRED

def test_g1_policy_limits_facts():
    validator = PortValidator()
    # Mais factos que o máximo (20)
    facts = [f"F{i}" for i in range(25)]
    p = AgentProposal(proposal_id="P-LIM-03", case_id="C-LIM-03", action="approve",
                      amount=10000.0, term_months=12, dsti_ratio=30.0, facts_cited=facts)
    assert validator.validate(p).outcome == OutcomeEnum.REPAIRED
