FROM python:3.12-slim AS base
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

FROM base AS builder
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -e .

FROM base AS runtime
COPY --from=builder /usr/local /usr/local
COPY src/ src/
COPY tests/ tests/
COPY benchmarks/ benchmarks/
COPY examples/ examples/
COPY docs/ docs/

CMD ["pytest", "tests/", "-v", "--tb=short"]
