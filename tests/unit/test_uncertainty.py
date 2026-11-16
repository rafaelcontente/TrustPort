from trust_net_port.schema.contracts import AgentProposal
from trust_net_port.validator import ConformalUncertaintyEstimator


def test_uncertainty_estimator_base():
    est = ConformalUncertaintyEstimator(base_uncertainty=2.5)
    proposal = AgentProposal(
        proposal_id="P-1", case_id="C-1", action="approve",
        amount=10000, term_months=12, dsti_ratio=25.0,
        facts_cited=["F1", "F2", "F3"] # 3 facts = 0 penalty
    )
    # 2.5 base + 0 fact penalty + 0 dsti penalty (25 <= 30)
    assert est.calculate_upper_bound(proposal) == 2.5

def test_uncertainty_estimator_penalties():
    est = ConformalUncertaintyEstimator(base_uncertainty=2.5)
    proposal = AgentProposal(
        proposal_id="P-2", case_id="C-2", action="approve",
        amount=50000, term_months=60, dsti_ratio=38.0,
        facts_cited=["F1"] # 1 fact = (3-1)*1.5 = 3.0 penalty
    )
    # 2.5 base + 3.0 fact penalty + 1.6 dsti penalty ((38-30)/10 * 2.0)
    assert est.calculate_upper_bound(proposal) == 7.1
