import pytest
import time
from trust_net_port.schema.contracts import AgentProposal
from trust_net_port.validator import PortValidator

def test_performance_latency_and_throughput():
    """Mede latência p50/p95/p99 e throughput."""
    validator = PortValidator()
    proposal = AgentProposal(
        proposal_id="P-PERF-01", case_id="C-PERF-01", action="approve",
        amount=10000.0, term_months=12, dsti_ratio=30.0, facts_cited=["F-1", "F-2", "F-3"]
    )
    
    n = 1000
    latencies = []
    start = time.perf_counter()
    for _ in range(n):
        t0 = time.perf_counter()
        validator.validate(proposal)
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000)  # ms
    
    total_time = time.perf_counter() - start
    latencies.sort()
    
    p50 = latencies[int(n * 0.50)]
    p95 = latencies[int(n * 0.95)]
    p99 = latencies[int(n * 0.99)]
    throughput = n / total_time
    
    print(f"\n--- Performance Metrics ---")
    print(f"Throughput: {throughput:.2f} proposals/sec")
    print(f"Latency p50: {p50:.3f} ms")
    print(f"Latency p95: {p95:.3f} ms")
    print(f"Latency p99: {p99:.3f} ms")
    print(f"---------------------------\n")
    
    # Asserts básicos de performance (ajustar conforme ambiente)
    assert p99 < 100, f"Latência p99 demasiado alta: {p99}ms"
    assert throughput > 100, f"Throughput demasiado baixo: {throughput} req/s"
