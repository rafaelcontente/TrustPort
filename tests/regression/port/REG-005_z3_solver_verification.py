import pytest
from trust_net_port.schema.contracts import AgentProposal
from trust_net_port.solver.z3_verifier import verify_proposal_constraints

def test_z3_accepts_valid_proposal():
    proposal = AgentProposal(proposal_id="P-100", case_id="C-TEST", action="approve", amount=40000, term_months=60, dsti_ratio=35.0, facts_cited=["F-221", "F-222"])
    is_valid, reason = verify_proposal_constraints(proposal)
    assert is_valid is True
    assert reason == "Constraints satisfied"

def test_z3_rejects_negative_amount():
    proposal = AgentProposal(proposal_id="P-101", case_id="C-TEST", action="approve", amount=-5000, term_months=60, dsti_ratio=35.0, facts_cited=["F-221"])
    is_valid, reason = verify_proposal_constraints(proposal)
    assert is_valid is False
    assert "Unsatisfiable" in reason

def test_z3_rejects_high_dsti():
    proposal = AgentProposal(proposal_id="P-102", case_id="C-TEST", action="approve", amount=40000, term_months=60, dsti_ratio=45.0, facts_cited=["F-221"])
    is_valid, reason = verify_proposal_constraints(proposal)
    assert is_valid is False
    assert "Unsatisfiable" in reason
