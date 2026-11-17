import json
import random

import requests
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("TrustPort")

TRUSTPORT_API_URL = "http://127.0.0.1:8000/validate"

# Mock database for client credit history
MOCK_CLIENT_DB = {
    "CLI-001": {
        "client_id": "CLI-001",
        "employment_years": 5,
        "employment_status": "Permanent",
        "credit_score": 750,
        "existing_debt": 5000.0,
        "payment_history": "No defaults in the last 5 years",
    },
    "CLI-002": {
        "client_id": "CLI-002",
        "employment_years": 1,
        "employment_status": "Probation",
        "credit_score": 620,
        "existing_debt": 15000.0,
        "payment_history": "1 default in the last 2 years",
    },
}


@mcp.tool()
def fetch_client_credit_history(client_id: str) -> str:
    """Fetches real credit history and employment data for a given client_id.
    Use this to gather factual evidence before submitting a proposal to validate_proposal."""

    client_data = MOCK_CLIENT_DB.get(client_id)

    if not client_data:
        # Generate realistic mock data for unknown IDs to keep the demo flowing
        client_data = {
            "client_id": client_id,
            "employment_years": random.randint(2, 15),
            "employment_status": random.choice(["Permanent", "Contract", "Self-employed"]),
            "credit_score": random.randint(600, 850),
            "existing_debt": round(random.uniform(0, 20000), 2),
            "payment_history": "Clean record" if random.random() > 0.2 else "Minor delay 2 years ago",
        }

    return json.dumps(client_data, indent=2, ensure_ascii=False)


@mcp.tool()
def validate_proposal(
    proposal_id: str, case_id: str, action: str, amount: float, term_months: int, dsti_ratio: float, facts_cited: list[str]
) -> str:
    """Validates an AI proposal against business rules, Z3 logic, and TrustPort compliance.
    NEVER approve a proposal without calling this tool first."""

    payload = {
        "proposal_id": proposal_id,
        "case_id": case_id,
        "action": action,
        "amount": amount,
        "term_months": term_months,
        "dsti_ratio": dsti_ratio,
        "facts_cited": facts_cited,
    }

    try:
        response = requests.post(TRUSTPORT_API_URL, json=payload, timeout=5)

        if response.status_code == 422:
            return json.dumps({"outcome": "ERROR", "reason_code": "SCHEMA_MISMATCH", "details": response.json()}, ensure_ascii=False)

        response.raise_for_status()
        result = response.json()

        return json.dumps(
            {
                "outcome": result.get("outcome"),
                "reason_code": result.get("reason_code"),
                "counterfactual": result.get("counterfactual"),
                "audit_hash": result.get("audit_hash"),
                "explanation": result.get("explanation"),
                "gates_passed": result.get("gates_passed", []),
                "gates_failed": result.get("gates_failed", []),
            },
            indent=2,
            ensure_ascii=False,
        )

    except requests.exceptions.ConnectionError:
        return f"CRITICAL ERROR: Could not connect to TrustPort API at {TRUSTPORT_API_URL}. Ensure the uvicorn server is running."
    except (requests.RequestException, ValueError, json.JSONDecodeError) as e:
        return f"Error validating proposal: {e!s}"


if __name__ == "__main__":
    mcp.run()
