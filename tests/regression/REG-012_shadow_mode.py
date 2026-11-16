import pytest
from trust_net_port.schema.contracts import AgentProposal, OutcomeEnum
from trust_net_port.validator import PortValidator

def test_shadow_mode_approves_but_logs_real_decision():
    """Em shadow mode, propostas que seriam recusadas são aprovadas, mas o motivo real é registado."""
    validator = PortValidator()
    validator.set_shadow_mode(True)
    
    # Proposta que falharia no G2 (DSTI 50% > 40%)
    proposal = AgentProposal(
        proposal_id="P-SHADOW-01", case_id="C-SHADOW-01", action="approve",
        amount=10000.0, term_months=12, dsti_ratio=50.0, facts_cited=["F-1", "F-2", "F-3"]
    )
    
    result = validator.validate(proposal)
    
    # Outcome é APPROVED (shadow)
    assert result.outcome == OutcomeEnum.APPROVED
    assert result.reason_code == "SHADOW-00"
    
    # Mas o shadow_outcome revela a decisão real
    assert result.shadow_outcome == "REFUSED"
    assert result.shadow_reason_code == "RUL-01"

def test_shadow_mode_disabled_behaves_normally():
    """Com shadow mode desligado, o sistema bloqueia normalmente."""
    validator = PortValidator()
    validator.set_shadow_mode(False)
    
    proposal = AgentProposal(
        proposal_id="P-SHADOW-02", case_id="C-SHADOW-02", action="approve",
        amount=10000.0, term_months=12, dsti_ratio=50.0, facts_cited=["F-1", "F-2", "F-3"]
    )
    
    result = validator.validate(proposal)
    
    assert result.outcome == OutcomeEnum.REFUSED
    assert result.reason_code == "RUL-01"
    assert result.shadow_outcome is None
