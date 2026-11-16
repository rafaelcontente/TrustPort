"""
Example 2: Rule Violation
"""
from trust_net_port.schema.contracts import AgentProposal
from trust_net_port.validator import PortValidator

def main():
    proposal = AgentProposal(
        proposal_id="EX-002",
        case_id="C-9998",
        action="approve",
        amount=80000.0,
        term_months=60,
        dsti_ratio=48.0,
        facts_cited=["F-200"]
    )
    result = PortValidator().validate(proposal)
    print(f"Outcome: {result.outcome.value}")
    print(f"Reason: {result.reason_code}")
    if result.counterfactual:
        print(f"Counterfactual: {result.counterfactual}")

if __name__ == "__main__":
    main()
