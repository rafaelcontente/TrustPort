import hashlib
import json

from trust_net_port.schema.contracts import PortResult


class AuditLogger:
    def __init__(self, code_version: str = "1.0.0"):
        self.code_version = code_version
        self.last_hash: str | None = None

    def log_decision(self, result: PortResult, prev_hash: str | None = None) -> str:
        """Regista uma decisão e devolve o novo hash encadeado."""
        # Dados imutáveis do registo
        log_entry = {
            "proposal_id": result.correlation_id, # Usamos correlation_id como traço
            "outcome": result.outcome.value,
            "reason_code": result.reason_code,
            "gates_passed": result.gates_passed,
            "gates_failed": result.gates_failed,
            "policy_version": result.policy_version,
            "code_version": self.code_version,
            "evaluated_at": result.evaluated_at,
            "prev_hash": prev_hash or self.last_hash or "GENESIS"
        }
        
        # Serialização determinística (sorted keys)
        payload = json.dumps(log_entry, sort_keys=True, separators=(',', ':'))
        
        # Hash SHA-256 do payload + hash anterior (encadeamento)
        hash_input = f"{payload}{log_entry['prev_hash']}".encode()
        new_hash = hashlib.sha256(hash_input).hexdigest()
        
        self.last_hash = new_hash
        return new_hash

    def verify_chain(self, logs: list[dict]) -> bool:
        """Verifica a integridade de uma cadeia de logs."""
        current_hash = "GENESIS"
        for log in logs:
            # Reconstruir o payload esperado
            expected_payload = json.dumps({
                "proposal_id": log["proposal_id"],
                "outcome": log["outcome"],
                "reason_code": log["reason_code"],
                "gates_passed": log["gates_passed"],
                "gates_failed": log["gates_failed"],
                "policy_version": log["policy_version"],
                "code_version": log["code_version"],
                "evaluated_at": log["evaluated_at"],
                "prev_hash": log["prev_hash"]
            }, sort_keys=True, separators=(',', ':'))
            
            expected_hash_input = f"{expected_payload}{log['prev_hash']}".encode()
            hashlib.sha256(expected_hash_input).hexdigest()
            
            # O hash armazenado no próximo log (ou o último) deve bater
            # Nota: nesta verificação simplificada, assumimos que o log tem um campo 'hash'
            # ou verificamos se o prev_hash do próximo bate com este cálculo.
            # Para este teste, vamos verificar se o prev_hash do log atual é igual ao hash calculado do anterior
            if log["prev_hash"] != current_hash:
                return False
            
            # Atualizar current_hash para a iteração seguinte (simulando o que o logger faria)
            current_hash = hashlib.sha256(f"{expected_payload}{log['prev_hash']}".encode()).hexdigest()
            
        return True
