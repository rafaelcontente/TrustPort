from z3 import Int, Or, Real, Solver, sat

from trust_net_port.schema.contracts import AgentProposal


def verify_constraints(
    proposal: AgentProposal, 
    high_amount_threshold: float = 50000.0, 
    min_term: int = 36,
    max_term: int = 120
) -> tuple[bool, str]:
    s = Solver()
    amount = Real('amount')
    term = Int('term')
    
    s.add(amount > 0)
    s.add(term > 0)
    
    # Restrição 1: Montante alto exige prazo longo
    s.add(Or(amount <= high_amount_threshold, term >= min_term))
    # Restrição 2: Prazo máximo absoluto
    s.add(term <= max_term)
    
    s.add(amount == proposal.amount)
    s.add(term == proposal.term_months)
    
    if s.check() == sat:
        return True, "Constraints satisfied"
    else:
        return False, f"SMT-01: Violates formal constraints (max term {max_term}m, or amount > {high_amount_threshold} requires term >= {min_term}m)."
