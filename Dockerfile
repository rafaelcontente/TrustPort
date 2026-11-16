FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src/ src/
COPY tests/ tests/
COPY benchmarks/ benchmarks/
COPY examples/ examples/

RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -e .

CMD ["pytest", "tests/", "-v"]
