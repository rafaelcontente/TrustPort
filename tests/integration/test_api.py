"""Integration tests for FastAPI HTTP endpoints."""

from fastapi.testclient import TestClient

from trust_net_port.api import app

client = TestClient(app)


def test_health_check():
    """Health endpoint returns 200."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_validate_approved_proposal():
    """Valid proposal returns APPROVED."""
    proposal = {
        "proposal_id": "P-API-01",
        "case_id": "C-API-01",
        "action": "approve",
        "amount": 10000.0,
        "term_months": 12,
        "dsti_ratio": 0.30,
        "facts_cited": ["F-1", "F-2", "F-3"],
    }
    response = client.post("/validate", json=proposal)
    assert response.status_code == 200
    data = response.json()
    assert data["outcome"] == "APPROVED"
    assert data["reason_code"] == "OK-00"
    assert len(data["gates_passed"]) == 5


def test_validate_refused_proposal():
    """Invalid proposal returns REFUSED with counterfactual."""
    proposal = {
        "proposal_id": "P-API-02",
        "case_id": "C-API-02",
        "action": "approve",
        "amount": 10000.0,
        "term_months": 12,
        "dsti_ratio": 0.50,  # Exceeds 40% limit
        "facts_cited": ["F-1", "F-2", "F-3"],
    }
    response = client.post("/validate", json=proposal)
    assert response.status_code == 200
    data = response.json()
    assert data["outcome"] == "REFUSED"
    assert data["reason_code"] == "RUL-01"
    assert "counterfactual" in data
    assert "Reduce DSTI" in data["counterfactual"]


def test_validate_invalid_schema():
    """Invalid schema returns 422."""
    proposal = {
        "proposal_id": "P-API-03",
        "case_id": "C-API-03",
        "action": "approve",
        "amount": -1000.0,  # Invalid: negative amount
        "term_months": 12,
        "dsti_ratio": 0.30,
        "facts_cited": ["F-1"],
    }
    response = client.post("/validate", json=proposal)
    assert response.status_code == 200
    data = response.json()
    assert data["outcome"] == "REPAIRED"
    assert data["reason_code"] == "SCH-01"


def test_stats_endpoint():
    """Stats endpoint returns decision count."""
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_decisions" in data
    assert "chain_valid" in data
    assert data["chain_valid"] is True
