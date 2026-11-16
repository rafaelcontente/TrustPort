#!/bin/bash
set -e
echo "🚀 Reproducing TrustPort Benchmark..."
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -q -e .
else
    source .venv/bin/activate
fi
python benchmarks/run.py
echo "✅ Benchmark reproduced successfully."
