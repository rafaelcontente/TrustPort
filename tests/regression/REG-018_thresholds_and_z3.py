from trust_net_port.schema.contracts import AgentProposal, OutcomeEnum
from trust_net_port.validator import PortValidator


def test_g2_exact_thresholds():
    validator = PortValidator()
    # 39.99% deve passar
    p1 = AgentProposal(proposal_id="P1", case_id="C1", action="approve", amount=10000, term_months=12, dsti_ratio=39.99, facts_cited=["F1", "F2", "F3"])
    assert validator.validate(p1).outcome == OutcomeEnum.APPROVED
    
    # 40.0% deve passar (limite inclusivo na política <= 40%)
    p2 = AgentProposal(proposal_id="P2", case_id="C2", action="approve", amount=10000, term_months=12, dsti_ratio=40.0, facts_cited=["F1", "F2", "F3"])
    assert validator.validate(p2).outcome == OutcomeEnum.APPROVED
    
    # 40.01% deve falhar
    p3 = AgentProposal(proposal_id="P3", case_id="C3", action="approve", amount=10000, term_months=12, dsti_ratio=40.01, facts_cited=["F1", "F2", "F3"])
    assert validator.validate(p3).outcome == OutcomeEnum.REFUSED

def test_g3_isolated_and_multiple_violations():
    validator = PortValidator()
    # Violação isolada 1: Montante alto, prazo curto
    p1 = AgentProposal(proposal_id="P4", case_id="C4", action="approve", amount=60000, term_months=12, dsti_ratio=30.0, facts_cited=["F1", "F2", "F3"])
    r1 = validator.validate(p1)
    assert r1.outcome == OutcomeEnum.REFUSED
    assert r1.reason_code == "SMT-01"
    
    # Violação isolada 2: Montante baixo, prazo acima do máximo (120)
    p2 = AgentProposal(proposal_id="P5", case_id="C5", action="approve", amount=10000, term_months=150, dsti_ratio=30.0, facts_cited=["F1", "F2", "F3"])
    r2 = validator.validate(p2)
    assert r2.outcome == OutcomeEnum.REFUSED
    assert r2.reason_code == "SMT-01"
    
    # Múltiplas violações simultâneas
    p3 = AgentProposal(proposal_id="P6", case_id="C6", action="approve", amount=60000, term_months=150, dsti_ratio=30.0, facts_cited=["F1", "F2", "F3"])
    r3 = validator.validate(p3)
    assert r3.outcome == OutcomeEnum.REFUSED
    assert r3.reason_code == "SMT-01"

def test_g3_timeout_fail_closed():
    from unittest.mock import patch
    validator = PortValidator()
    proposal = AgentProposal(proposal_id="P7", case_id="C7", action="approve", amount=60000, term_months=48, dsti_ratio=30.0, facts_cited=["F1", "F2", "F3"])
    
    with patch('trust_net_port.validator.verify_constraints', side_effect=TimeoutError("Z3 solver timeout")):
        result = validator.validate(proposal)
        assert result.outcome == OutcomeEnum.REFUSED
        assert result.reason_code == "SMT-ERR"
        assert "timeout" in result.explanation.lower()
