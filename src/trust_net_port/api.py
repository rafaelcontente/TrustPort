"""FastAPI HTTP wrapper for TrustPort validator.

Exposes the validation pipeline as a REST API with automatic OpenAPI spec.
"""

from fastapi import FastAPI, HTTPException
from pydantic import ValidationError

from trust_net_port.audit.store import AuditStore
from trust_net_port.schema.contracts import AgentProposal, PortResult
from trust_net_port.validator import PortValidator

app = FastAPI(
    title="TrustPort API",
    description="Mandatory validation pipeline for AI-mediated decisions",
    version="1.0.0",
)

validator = PortValidator()
audit_store = AuditStore()


@app.post("/validate", response_model=PortResult, summary="Validate a proposal")
def validate_proposal(proposal: AgentProposal) -> PortResult:
    """Validate an AI proposal through all 5 gates.
    
    Returns a typed verdict: APPROVED, REPAIRED, ESCALATED, or REFUSED.
    Every refusal includes an actionable counterfactual.
    """
    try:
        result = validator.validate(proposal)
        audit_store.log(result)
        return result
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Internal error: {e!s}")


@app.get("/health", summary="Health check")
def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/stats", summary="Validation statistics")
def get_stats():
    """Return basic statistics about logged decisions."""
    return {
        "total_decisions": audit_store.count(),
        "chain_valid": audit_store.verify_chain(),
    }
