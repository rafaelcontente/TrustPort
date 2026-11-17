import json
import random
from pathlib import Path

from trust_net_port.schema.contracts import AgentProposal
from trust_net_port.validator import PortValidator


def generate_synthetic_dataset(n=1000, seed=42):
    random.seed(seed)
    proposals = []
    for i in range(n):
        # 70% valid-ish, 15% schema invalid, 15% rule/uncertainty invalid
        if i < 150:
            amount = -random.uniform(100, 1000)  # Invalid schema
            dsti = 30.0
            facts = []
        elif i < 300:
            amount = random.uniform(10000, 100000)
            dsti = random.uniform(41.0, 60.0)  # Invalid rule
            facts = ["F-1"]
        else:
            amount = random.uniform(10000, 50000)
            dsti = random.uniform(20.0, 39.0)
            facts = [f"F-{j}" for j in range(random.randint(1, 4))]

        proposals.append(
            AgentProposal(
                proposal_id=f"BENCH-{i:04d}",
                case_id=f"C-{i:04d}",
                action="approve",
                amount=amount,
                term_months=random.choice([12, 24, 36, 48, 60]),
                dsti_ratio=round(dsti, 2),
                facts_cited=facts,
            )
        )
    return proposals


def run_benchmark():
    validator = PortValidator()
    proposals = generate_synthetic_dataset(1000)

    results = {"APPROVED": 0, "REPAIRED": 0, "REFUSED": 0, "ESCALATED": 0}
    for p in proposals:
        res = validator.validate(p)
        results[res.outcome.value] += 1

    total = sum(results.values())
    summary = {
        "version": "0.1.0",
        "dataset_size": total,
        "seed": 42,
        "outcomes": results,
        "rates": {k: round(v / total, 4) for k, v in results.items()},
    }

    out_path = Path("benchmarks/results/baseline_v0.1.0.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2))
    print(f"Benchmark complete. Results saved to {out_path}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    run_benchmark()
