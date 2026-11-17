"""Test SQLite audit store with crash recovery and chain verification."""

import sqlite3

from trust_net_port.audit.store import AuditStore
from trust_net_port.schema.contracts import AgentProposal
from trust_net_port.validator import PortValidator


def test_sqlite_persistence(tmp_path):
    db_path = str(tmp_path / "audit.db")
    store = AuditStore(db_path=db_path, code_version="2.0.0")
    validator = PortValidator()
    proposal = AgentProposal(
        proposal_id="P-SQL-01",
        case_id="C-SQL-01",
        action="approve",
        amount=10000.0,
        term_months=12,
        dsti_ratio=0.30,
        facts_cited=["F-1", "F-2", "F-3"],
    )
    result = validator.validate(proposal)
    store.log(result)
    assert store.count() == 1
    assert store.verify_chain()
    store2 = AuditStore(db_path=db_path, code_version="2.0.0")
    assert store2.count() == 1
    assert store2.verify_chain()


def test_chain_integrity_after_tampering(tmp_path):
    db_path = str(tmp_path / "audit.db")
    store = AuditStore(db_path=db_path)
    validator = PortValidator()
    for i in range(3):
        proposal = AgentProposal(
            proposal_id=f"P-TAMPER-{i}",
            case_id=f"C-TAMPER-{i}",
            action="approve",
            amount=10000.0,
            term_months=12,
            dsti_ratio=0.30,
            facts_cited=["F-1", "F-2", "F-3"],
        )
        store.log(validator.validate(proposal))
    assert store.verify_chain()
    conn = sqlite3.connect(db_path)
    conn.execute("UPDATE audit_log SET outcome = 'REFUSED' WHERE id = 1")
    conn.commit()
    conn.close()
    assert not store.verify_chain()


def test_wal_mode_durability(tmp_path):
    db_path = str(tmp_path / "audit.db")
    AuditStore(db_path=db_path)
    conn = sqlite3.connect(db_path)
    mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
    conn.close()
    assert mode == "wal"
