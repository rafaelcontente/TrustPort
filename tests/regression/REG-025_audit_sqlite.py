"""Test SQLite audit store with crash recovery and chain verification."""

import os
import sqlite3

from trust_net_port.audit.store import AuditStore
from trust_net_port.schema.contracts import AgentProposal
from trust_net_port.validator import PortValidator


def test_sqlite_persistence():
    """Decisions persist to SQLite and survive process restart."""
    db_path = "test_audit.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    store = AuditStore(db_path=db_path, code_version="2.0.0")
    validator = PortValidator()
    
    proposal = AgentProposal(
        proposal_id="P-SQL-01", case_id="C-SQL-01", action="approve",
        amount=10000.0, term_months=12, dsti_ratio=30.0,
        facts_cited=["F-1", "F-2", "F-3"]
    )
    result = validator.validate(proposal)
    store.log(result)
    
    assert store.count() == 1
    assert store.verify_chain()
    
    # Simulate "restart" by creating new store instance
    store2 = AuditStore(db_path=db_path, code_version="2.0.0")
    assert store2.count() == 1
    assert store2.verify_chain()
    
    # Clean up
    os.remove(db_path)


def test_chain_integrity_after_tampering():
    """Altering any record breaks the chain."""
    db_path = "test_audit_tamper.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    store = AuditStore(db_path=db_path)
    validator = PortValidator()
    
    # Log 3 decisions
    for i in range(3):
        proposal = AgentProposal(
            proposal_id=f"P-TAMPER-{i}", case_id=f"C-TAMPER-{i}", action="approve",
            amount=10000.0, term_months=12, dsti_ratio=30.0,
            facts_cited=["F-1", "F-2", "F-3"]
        )
        result = validator.validate(proposal)
        store.log(result)
    
    assert store.count() == 3
    assert store.verify_chain()
    
    # Tamper with first record (change outcome)
    conn = sqlite3.connect(db_path)
    conn.execute("UPDATE audit_log SET outcome = 'REFUSED' WHERE id = 1")
    conn.commit()
    conn.close()
    
    # Chain should now be broken
    assert not store.verify_chain(), "Tampering was not detected!"
    
    # Clean up
    os.remove(db_path)


def test_wal_mode_durability():
    """SQLite WAL mode ensures writes are durable."""
    db_path = "test_audit_wal.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    AuditStore(db_path=db_path)
    
    # Check WAL mode is set
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("PRAGMA journal_mode")
    mode = cursor.fetchone()[0]
    conn.close()
    
    assert mode == "wal", f"Expected WAL mode, got {mode}"
    
    # Clean up
    os.remove(db_path)
