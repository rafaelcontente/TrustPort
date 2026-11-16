from z3 import Int, Or, Real, Solver, sat

from trust_net_port.schema.contracts import AgentProposal


def verify_constraints(proposal: AgentProposal, high_amount_threshold: float = 50000.0, min_term: int = 36) -> tuple[bool, str]:
    s = Solver()
    amount = Real('amount')
    term = Int('term')
    
    # Restrições básicas de sanidade
    s.add(amount > 0)
    s.add(term > 0)
    
    # NOVA RESTRIÇÃO G3: Montantes > 50k exigem prazo >= 36 meses
    s.add(Or(amount <= high_amount_threshold, term >= min_term))
    
    # Atribuir valores da proposta
    s.add(amount == proposal.amount)
    s.add(term == proposal.term_months)
    
    if s.check() == sat:
        return True, "Constraints satisfied"
    else:
        return False, "SMT-01: High amount (>{high_amount_threshold}) requires minimum term of 36 months."
