"""Append-only audit store with chained SHA-256 hashes.

Each decision is persisted to SQLite WAL mode. The hash chain ensures
tamper detection: altering any record breaks the chain for all subsequent records.
"""

import hashlib
import json
import sqlite3
import time
from pathlib import Path

from trust_net_port.schema.contracts import PortResult


class AuditStore:
    def __init__(self, db_path: str = "audit.db", code_version: str = "1.0.0"):
        self.db_path = Path(db_path)
        self.code_version = code_version
        self._init_db()

    def _init_db(self) -> None:
        """Create table with WAL mode for durability."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proposal_id TEXT NOT NULL,
                outcome TEXT NOT NULL,
                reason_code TEXT NOT NULL,
                gates_passed TEXT NOT NULL,
                gates_failed TEXT NOT NULL,
                policy_version TEXT NOT NULL,
                code_version TEXT NOT NULL,
                evaluated_at TEXT NOT NULL,
                prev_hash TEXT NOT NULL,
                hash TEXT NOT NULL,
                created_at REAL NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def log(self, result: PortResult) -> str:
        """Persist decision and return new hash."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        
        # Fetch last hash
        cursor = conn.execute("SELECT hash FROM audit_log ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        prev_hash = row[0] if row else "GENESIS"
        
        # Build log entry
        entry = {
            "proposal_id": result.correlation_id or "UNKNOWN",
            "outcome": result.outcome.value,
            "reason_code": result.reason_code,
            "gates_passed": result.gates_passed,
            "gates_failed": result.gates_failed,
            "policy_version": result.policy_version or "0.0.0",
            "code_version": self.code_version,
            "evaluated_at": result.evaluated_at or "",
            "prev_hash": prev_hash,
        }
        
        # Compute hash
        payload = json.dumps(entry, sort_keys=True, separators=(",", ":"))
        new_hash = hashlib.sha256(f"{payload}{prev_hash}".encode()).hexdigest()
        
        # Insert
        conn.execute("""
            INSERT INTO audit_log 
            (proposal_id, outcome, reason_code, gates_passed, gates_failed, 
             policy_version, code_version, evaluated_at, prev_hash, hash, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry["proposal_id"],
            entry["outcome"],
            entry["reason_code"],
            json.dumps(entry["gates_passed"]),
            json.dumps(entry["gates_failed"]),
            entry["policy_version"],
            entry["code_version"],
            entry["evaluated_at"],
            entry["prev_hash"],
            new_hash,
            time.time(),
        ))
        conn.commit()
        conn.close()
        return new_hash

    def verify_chain(self) -> bool:
        """Verify integrity of entire chain. Returns True if valid."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        cursor = conn.execute("""
            SELECT proposal_id, outcome, reason_code, gates_passed, gates_failed,
                   policy_version, code_version, evaluated_at, prev_hash, hash
            FROM audit_log ORDER BY id ASC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return True
        
        current_hash = "GENESIS"
        for row in rows:
            (proposal_id, outcome, reason_code, gates_passed, gates_failed,
             policy_version, code_version, evaluated_at, prev_hash, stored_hash) = row
            
            if prev_hash != current_hash:
                return False
            
            entry = {
                "proposal_id": proposal_id,
                "outcome": outcome,
                "reason_code": reason_code,
                "gates_passed": json.loads(gates_passed),
                "gates_failed": json.loads(gates_failed),
                "policy_version": policy_version,
                "code_version": code_version,
                "evaluated_at": evaluated_at,
                "prev_hash": prev_hash,
            }
            payload = json.dumps(entry, sort_keys=True, separators=(",", ":"))
            current_hash = hashlib.sha256(f"{payload}{prev_hash}".encode()).hexdigest()
            
            if current_hash != stored_hash:
                return False
        
        return True

    def count(self) -> int:
        """Return number of logged decisions."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        cursor = conn.execute("SELECT COUNT(*) FROM audit_log")
        count = cursor.fetchone()[0]
        conn.close()
        return count
