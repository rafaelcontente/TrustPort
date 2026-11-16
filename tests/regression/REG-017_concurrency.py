from concurrent.futures import ThreadPoolExecutor, as_completed

from trust_net_port.schema.contracts import AgentProposal, OutcomeEnum
from trust_net_port.validator import PortValidator


def test_concurrency_statelessness():
    """Parallel validations must not corrupt state or mix gates_passed lists."""
    validator = PortValidator()
    
    def run_validation(i):
        p = AgentProposal(
            proposal_id=f"P-CONC-{i}", case_id=f"C-CONC-{i}", action="approve",
            amount=10000.0, term_months=12, dsti_ratio=30.0, facts_cited=["F-1", "F-2", "F-3"]
        )
        return validator.validate(p)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(run_validation, i) for i in range(100)]
        results = [f.result() for f in as_completed(futures)]
        
    # All 100 must be APPROVED with exactly 5 gates passed
    for r in results:
        assert r.outcome == OutcomeEnum.APPROVED
        assert len(r.gates_passed) == 5
        # Ensure no list leakage (e.g., 10 gates passed)
        assert set(r.gates_passed) == {"G1_SCHEMA", "G2_RULES", "G3_SOLVER", "G4_UNCERTAINTY", "G5_FIDELITY"}
