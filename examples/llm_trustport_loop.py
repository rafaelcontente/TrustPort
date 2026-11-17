import json
import requests  # Preparado para a API real quando a tivermos

# 1. Definição da Ferramenta (Tool Schema) que a LLM "vê"
TRUSTPORT_TOOL_SCHEMA = {
    "name": "validate_proposal",
    "description": "Valida uma proposta de IA contra regras de negócio, lógica Z3 e conformidade. NUNCA aproves uma proposta sem chamar esta ferramenta primeiro.",
    "parameters": {
        "type": "object",
        "properties": {
            "domain": {"type": "string", "description": "O domínio da proposta (ex: 'credit_approval', 'real_estate')."},
            "proposed_action": {"type": "string", "description": "A ação que a IA quer executar."},
            "parameters": {"type": "object", "description": "Os parâmetros da proposta (ex: {'amount': 50000, 'dsti': 0.45})."}
        },
        "required": ["domain", "proposed_action", "parameters"]
    }
}

# 2. Simulação do Motor TrustPort (substitui por requests.post("http://localhost:8000/validate", json=...) quando a API estiver up)
def mock_trustport_gate(proposal: dict) -> dict:
    print(f"\n🛡️ [TrustPort] A validar proposta no Portão...")
    
    # Simulação baseada nas regras do teu README (G2 Rules / Z3)
    dsti = proposal["parameters"].get("dsti", 0.0)
    amount = proposal["parameters"].get("amount", 0)
    
    if dsti > 0.40:
        return {
            "outcome": "REFUSED",
            "reason_code": "G2-DSTI_EXCEEDED",
            "counterfactual": f"O DSTI de {dsti*100:.0f}% excede o limite de 40%. Para ser APPROVED, o DSTI deve ser <= 0.40 ou o montante deve ser reduzido.",
            "audit_hash": "sha256:8f4b2c..."
        }
    
    return {
        "outcome": "APPROVED",
        "reason_code": "G1-G5-PASS",
        "counterfactual": None,
        "audit_hash": "sha256:9a1e3d..."
    }

# 3. O Loop Agêntico (O que a LLM faz internamente)
def agent_loop(user_request: str):
    print(f"👤 Utilizador: {user_request}")
    
    # Iteração 1: A LLM gera uma proposta inicial (muitas vezes otimista/errada)
    current_proposal = {
        "domain": "credit_approval",
        "proposed_action": "Aprovar empréstimo pessoal",
        "parameters": {"amount": 50000, "dsti": 0.45}  # DSTI de 45% (Violação da Regra G2)
    }
    
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        print(f"\n🔄 Tentativa {attempt}: A LLM submeteu a proposta:")
        print(json.dumps(current_proposal, indent=2))
        
        # Chamada à Ferramenta TrustPort
        result = mock_trustport_gate(current_proposal)
        
        print(f"\n📋 [TrustPort Result]: {result['outcome']} | Código: {result['reason_code']}")
        if result['counterfactual']:
            print(f"💡 Counterfactual para a LLM: '{result['counterfactual']}'")
            
        if result['outcome'] == 'APPROVED':
            print("\n✅ [SUCESSO] A proposta cumpre todas as regras do TrustPort. Pode ser executada.")
            return current_proposal
            
        elif result['outcome'] in ['REFUSED', 'REPAIRED']:
            print("🧠 [LLM] A processar o counterfactual e a reparar a proposta...")
            # Simulação da LLM a reparar a proposta com base no counterfactual
            current_proposal["parameters"]["dsti"] = 0.38  # A LLM "percebeu" e ajustou o DSTI para 38%
            
    print("\n❌ [FALHA] A LLM não conseguiu gerar uma proposta válida dentro do limite de tentativas.")
    return None

# Executar o teste
if __name__ == "__main__":
    agent_loop("Quero um empréstimo de 50k com DSTI de 45%")
