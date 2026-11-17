import json
import uuid

import requests

TRUSTPORT_API_URL = "http://127.0.0.1:8000/validate"


def call_trustport_api(proposal: dict) -> dict:
    print(f"\n🛡️ [TrustPort API] A validar proposta em {TRUSTPORT_API_URL}...")
    try:
        api_payload = {
            "proposal_id": proposal.get("proposal_id", str(uuid.uuid4())),
            "case_id": proposal.get("case_id", "CASE-001"),
            "action": proposal.get("proposed_action", "approve_loan"),
            "amount": proposal["parameters"].get("amount", 50000),
            "term_months": proposal["parameters"].get("term_months", 60),
            "dsti_ratio": proposal["parameters"].get("dsti_ratio", 0.45),
            "facts_cited": proposal.get("facts_cited", []),
        }

        response = requests.post(TRUSTPORT_API_URL, json=api_payload, timeout=5)
        if response.status_code == 422:
            return {"outcome": "ERROR", "reason_code": "SCHEMA_MISMATCH", "details": response.json()}
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError) as e:
        return {"outcome": "ERROR", "reason_code": "API_ERROR", "details": str(e)}


def agent_loop_real(user_request: str):
    print(f"👤 Utilizador: {user_request}\n")

    current_proposal = {
        "proposal_id": "PROP-001",
        "case_id": "CASE-001",
        "proposed_action": "approve_loan",
        "parameters": {"amount": 50000, "term_months": 60, "dsti_ratio": 0.45},
        "facts_cited": ["Rendimento mensal: 3000€", "Prestação pretendida: 1350€ (DSTI 45%)"],
    }

    for attempt in range(1, 4):
        print(f"{'=' * 60}\n🔄 Tentativa {attempt}:")
        print(json.dumps(current_proposal, indent=2, ensure_ascii=False))

        result = call_trustport_api(current_proposal)

        print(f"\n📋 [TrustPort Result]: {result.get('outcome', 'UNKNOWN')} | Código: {result.get('reason_code', 'N/A')}")
        if result.get("counterfactual"):
            print(f"💡 Counterfactual: '{result['counterfactual']}'")
        if result.get("audit_hash"):
            print(f"🔒 Audit Hash: {result['audit_hash']}")

        if result.get("outcome") == "APPROVED":
            print("\n✅ [SUCESSO] Proposta aprovada pelo TrustPort! Pode ser executada.")
            return

        elif result.get("outcome") in ["REFUSED", "REPAIRED", "ESCALATED"]:
            print("🧠 [LLM Simulado] A processar counterfactual e a reparar a proposta...")

            # A LLM "percebe" que precisa de corrigir o DSTI (Gate 2) E adicionar mais factos (Gate 4)
            current_proposal["parameters"]["dsti_ratio"] = 0.38
            current_proposal["facts_cited"] = [
                "Rendimento mensal: 3000€",
                "Prestação ajustada: 1140€ (DSTI 38%)",
                "Histórico de crédito: Impecável, sem incumprimentos nos últimos 5 anos",  # <-- O 3º facto baixa a penalidade de incerteza!
            ]


if __name__ == "__main__":
    agent_loop_real("Quero um empréstimo de 50k com DSTI de 45%")
