from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

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
    facts_cited: List[str]

class PortResult(BaseModel):
    outcome: OutcomeEnum
    reason_code: str
    gates_passed: List[str]
    gates_failed: List[str]
    counterfactual: Optional[str] = None
    explanation: Optional[str] = None