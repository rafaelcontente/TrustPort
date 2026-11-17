import json
import requests
from mcp.server.fastmcp import FastMCP

# Inicializar o servidor FastMCP
mcp = FastMCP("TrustPort")

TRUSTPORT_API_URL = "http://127.0.0.1:8000/validate"

@mcp.tool()
def validate_proposal(
    proposal_id: str,
    case_id: str,
    action: str,
    amount: float,
    term_months: int,
    dsti_ratio: float,
    facts_cited: list[str]
) -> str:
    """Valida uma proposta de IA contra regras de negócio, lógica Z3 e conformidade do TrustPort. 
    NUNCA aproves uma proposta sem chamar esta ferramenta primeiro."""
    
    payload = {
        "proposal_id": proposal_id,
        "case_id": case_id,
        "action": action,
        "amount": amount,
        "term_months": term_months,
        "dsti_ratio": dsti_ratio,
        "facts_cited": facts_cited
    }
    
    try:
        response = requests.post(TRUSTPORT_API_URL, json=payload, timeout=5)
        
        if response.status_code == 422:
            return json.dumps({
                "outcome": "ERROR",
                "reason_code": "SCHEMA_MISMATCH",
                "details": response.json()
            }, ensure_ascii=False)
            
        response.raise_for_status()
        result = response.json()
        
        return json.dumps({
            "outcome": result.get("outcome"),
            "reason_code": result.get("reason_code"),
            "counterfactual": result.get("counterfactual"),
            "audit_hash": result.get("audit_hash"),
            "explanation": result.get("explanation"),
            "gates_passed": result.get("gates_passed", []),
            "gates_failed": result.get("gates_failed", [])
        }, indent=2, ensure_ascii=False)
        
    except requests.exceptions.ConnectionError:
        return f"ERRO CRÍTICO: Não foi possível ligar à API do TrustPort em {TRUSTPORT_API_URL}. Certifica-te que o servidor uvicorn está a correr."
    except Exception as e:
        return f"Erro ao validar proposta: {str(e)}"

if __name__ == "__main__":
    mcp.run()
