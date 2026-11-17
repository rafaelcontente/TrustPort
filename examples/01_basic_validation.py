"""
Example 1: Basic Validation
"""

from trust_net_port.schema.contracts import AgentProposal
from trust_net_port.validator import PortValidator


def main():
    proposal = AgentProposal(
        proposal_id="EX-001",
        case_id="C-9999",
        action="approve",
        amount=25000.0,
        term_months=36,
        dsti_ratio=28.5,
        facts_cited=["F-100", "F-101", "F-102"],
    )
    result = PortValidator().validate(proposal)
    print(f"Outcome: {result.outcome.value}")
    print(f"Reason: {result.reason_code}")
    if result.explanation:
        print(f"Explanation: {result.explanation}")


if __name__ == "__main__":
    main()
