from enum import Enum

from pydantic import BaseModel


class OutcomeEnum(str, Enum):
    APPROVED = "APPROVED"
    REPAIRED = "REPAIRED"
    ESCALATED = "ESCALATED"
    REFUSED = "REFUSED"

class AgentProposal(BaseModel):
    proposal_id: str
    case_id: str
    action: str
    amount: float
    term_months: int
    dsti_ratio: float
    facts_cited: list[str]

class PortResult(BaseModel):
    outcome: OutcomeEnum
    reason_code: str
    gates_passed: list[str]
    gates_failed: list[str]
    counterfactual: str | None = None
    explanation: str | None = None