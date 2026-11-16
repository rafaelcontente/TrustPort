from z3 import Real, Solver, And, sat
from ..schema.contracts import AgentProposal

def verify_proposal_constraints(proposal: AgentProposal) -> tuple[bool, str]:
    """
    Uses Z3 to formally verify that the proposal satisfies hard domain constraints.
    Returns (is_valid, reason).
    """
    s = Solver()
    
    # Define symbolic variables
    amount = Real('amount')
    dsti = Real('dsti')
    facts_count = Real('facts_count')
    
    # Add constraints from the proposal
    s.add(amount == proposal.amount)
    s.add(dsti == proposal.dsti_ratio)
    s.add(facts_count == len(proposal.facts_cited))
    
    # Add hard domain rules (Policy-as-Code)
    rules = And(
        amount > 0,
        dsti >= 0,
        dsti <= 40.0,
        facts_count >= 1
    )
    s.add(rules)
    
    # Check satisfiability
    if s.check() == sat:
        return True, "Constraints satisfied"
    else:
        return False, "Unsatisfiable constraints (formal violation)"
