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
        # 1. Validar a proposta
        result = validator.validate(proposal)
        
        # 2. Guardar na auditoria e obter o hash
        audit_hash = audit_store.log(result)
        
        # 3. Atualizar o modelo Pydantic de forma segura (Pydantic v2)
        # Nota: Se 'audit_hash' não for um campo em PortResult, isto dará erro.
        # É por isso que preciso de ver o contracts.py no Passo 1.
        result = result.model_copy(update={"audit_hash": audit_hash})
        
        return result
        
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:  # noqa: BLE001
        # Isto vai imprimir o erro real no terminal do Uvicorn
        import traceback
        print(f"❌ ERRO INTERNO NO VALIDATOR: {e}")
        traceback.print_exc()
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
