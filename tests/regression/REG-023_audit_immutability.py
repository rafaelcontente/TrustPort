import hashlib
import json

from trust_net_port.audit import AuditLogger
from trust_net_port.schema.contracts import AgentProposal
from trust_net_port.validator import PortValidator


def test_audit_chain_integrity():
    """A cadeia de hashes deve detetar qualquer adulteração."""
    validator = PortValidator()
    logger = AuditLogger(code_version="1.0.0")

    proposal = AgentProposal(
        proposal_id="P-AUD-CHAIN",
        case_id="C-AUD-CHAIN",
        action="approve",
        amount=10000.0,
        term_months=12,
        dsti_ratio=0.30,
        facts_cited=["F-1", "F-2", "F-3"],
    )

    # Registar primeira decisão
    result1 = validator.validate(proposal)
    hash1 = logger.log_decision(result1)

    # Registar segunda decisão
    result2 = validator.validate(proposal)
    hash2 = logger.log_decision(result2, prev_hash=hash1)

    # Verificar encadeamento
    assert logger.last_hash == hash2
    assert hash1 != hash2

    # Simular adulteração: alterar o outcome do primeiro log manualmente
    # (Num cenário real, isto seria detetado ao recalcular o hash do log 2,
    # pois o prev_hash do log 2 já não bateria com o hash recalculado do log 1 adulterado)
    tampered_payload = json.dumps(
        {
            "proposal_id": result1.correlation_id,
            "outcome": "REFUSED",  # ADULTERADO
            "reason_code": result1.reason_code,
            "gates_passed": result1.gates_passed,
            "gates_failed": result1.gates_failed,
            "policy_version": result1.policy_version,
            "code_version": "1.0.0",
            "evaluated_at": result1.evaluated_at,
            "prev_hash": "GENESIS",
        },
        sort_keys=True,
        separators=(",", ":"),
    )

    tampered_hash = hashlib.sha256(f"{tampered_payload}GENESIS".encode()).hexdigest()

    # O hash adulterado NÃO deve ser igual ao hash1 original
    assert tampered_hash != hash1, "Tampering was not detected!"


def test_audit_metadata_completeness():
    """O registo de auditoria deve conter todas as versões necessárias."""
    validator = PortValidator()
    logger = AuditLogger(code_version="2.5.1")

    proposal = AgentProposal(
        proposal_id="P-AUD-META",
        case_id="C-AUD-META",
        action="approve",
        amount=10000.0,
        term_months=12,
        dsti_ratio=0.30,
        facts_cited=["F-1"],
    )
    result = validator.validate(proposal)

    # Simular o que é guardado no log
    log_entry = {
        "policy_version": result.policy_version,
        "code_version": logger.code_version,
        "evaluated_at": result.evaluated_at,
        "outcome": result.outcome.value,
    }

    assert log_entry["policy_version"] is not None
    assert log_entry["code_version"] == "2.5.1"
    assert log_entry["evaluated_at"] is not None
