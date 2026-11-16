# 🧠 Design Philosophy

Why TrustPort was built this way, what was considered, and what was rejected.
This is not a tutorial. It is a defense of the architecture.

## The Manifesto

An LLM will approve a loan it should refuse — fluently, confidently, and without
checking a single rule. The industry response has been to add more LLMs: a judge
model, a critic model, a reflection loop. This is building a house of cards and
calling it structural engineering.

TrustPort takes the opposite bet: **the model proposes, deterministic code decides.**
Not because LLMs are useless, but because in credit and compliance, the cost of a
false approval is asymmetric and severe. A wrong refusal costs a customer an
application cycle. A wrong approval costs a bank capital, a regulator a fine, and
a company its license.

The question the system answers is not "is this output good?" but "can this output
provably reach a human?" That is a different question, and it demands a different
architecture.

## Why Five Serial Gates (Not One Validator, Not Parallel)

**Rejected: a single monolithic validator.** One function that checks everything.
Problem: when it fails, you cannot tell which layer broke. Auditability dies.
A compliance officer cannot trace a refusal to a specific rule.

**Rejected: parallel gates with aggregation.** Run all five at once, combine results.
Problem: gate ordering is semantic. G1 (schema) must precede G3 (Z3) because Z3
cannot parse malformed input. Parallel execution would require every gate to be
defensive against garbage, duplicating validation logic.

**Chosen: serial fail-fast gates.** The first gate to say no stops the run. This
gives three properties:
1. Determinism: same input always follows the same path.
2. Traceability: `gates_passed` and `gates_failed` are a literal execution trace.
3. Cost efficiency: cheap checks (schema) run before expensive ones (Z3).

The cost is latency on the happy path (five checks instead of one). For a system
doing <100 req/s in a credit pilot, that latency is irrelevant. The auditability
gain is not.

## G1: Schema — Why Pydantic Over JSON Schema, Over Manual Validation

**Rejected: manual `if` checks.** The first version had them. Problem: they drift.
Someone adds a field to the contract, forgets the check, and a proposal with a
missing `dsti_ratio` slips through as None.

**Rejected: JSON Schema (draft 2020-12).** Standard, portable, language-agnostic.
Problem: it validates structure but not semantics. It cannot express "amount must
be finite" without custom keywords, and custom keywords lose portability. Also:
two sources of truth (the schema file and the Python model) invite divergence.

**Chosen: Pydantic v2 models as the single source of truth.** The contract IS the
schema. Type checking at the boundary, validation at construction. G1 then only
adds policy limits (max_amount, min_term, max_facts) that the type system cannot
express. The split is clean: Pydantic owns "is this a well-formed proposal?",
G1 owns "is this proposal within policy bounds?".

**Honest limitation:** Pydantic does not catch `NaN` or `Infinity` in float fields
by default. G1 explicitly checks `math.isfinite()`. This was a real bug found by
Hypothesis (REG-026) — the property-based test generated `float('inf')` and the
original G1 let it pass. The fix is now locked by test.

## G2: Rules — Why Policy-as-Code JSON, Over Hardcoded, Over a Rules Engine

**Rejected: hardcoded thresholds.** `if dsti > 40:` in the code. Problem: changing
a threshold requires a code deploy, a PR, a review, a CI run. For a compliance
rule that changes quarterly, this is absurd.

**Rejected: a full rules engine (Drools, OpenFisca, Rego/OPA).** Powerful,
expressive, battle-tested. Problem: they are a second language to learn, a second
runtime to operate, and a second attack surface. For a single domain (credit) with
a handful of numeric rules, this is over-engineering. Rego especially: the cost of
running an OPA sidecar for one policy file is not justified.

**Chosen: a versioned JSON policy file (`policies.json`).** Read at startup,
injected into the validator. Every decision carries `policy_version` in the audit
log. Changing a threshold is a config change with a version bump, testable in CI
(REG-008 proves policy versioning works). The policy is small enough that a human
can read the whole file and know every rule in the system. That is a feature, not
a limitation.

## G3: Formal Verification — Why Z3, Over Prolog, Over SAT, Over "More Rules"

**Rejected: more G2-style rules.** The temptation was to encode "high amount needs
long term" as another `if`. Problem: it works for one rule. For ten interacting
constraints, you get a combinatorial explosion of `if` branches that nobody can
audit. Z3 reasons about the constraint system as a whole.

**Rejected: Prolog.** Logic programming, declarative, good for rule chains.
Problem: Prolog is not a solver — it is a proof search. It can hang on cyclic
rules, it has no concept of arithmetic bounds over reals (it is integer/term
oriented), and the Python integration (SWI-Prolog via subprocess) adds a runtime
dependency that complicates Docker and CI.

**Rejected: raw SAT (MiniSat, CaDiCaL).** The underlying engine of Z3. Problem:
SAT is propositional. Credit constraints are arithmetic over reals (amount, DSTI,
term). You would need to encode real arithmetic into bit-blasted SAT clauses —
reimplementing the SMT layer that Z3 already provides.

**Chosen: Z3 via the SMT-LIB interface.** It is the right abstraction level:
real arithmetic, integer bounds, implications, all in one solver. The Python
bindings are mature. The cost: Z3 is not thread-safe. This was discovered the
hard way under concurrent load (REG-017) and fixed with a `threading.Lock`. The
lock serializes Z3 calls — acceptable at pilot throughput, a bottleneck to solve
with solver pools at scale.

**The honest admission:** Z3 adds the most complexity to the system for the
smallest number of constraints (two, currently). If the constraint set never
grows beyond what `if` statements can express, Z3 is over-engineering. It is
included because the *architecture* should not have to change when compliance
complexity grows. The bet is that formal constraints will be needed, not that
they are needed today.

## G4: Uncertainty — Why Split Conformal, Over Bayesian, Over Quantile Regression, Over Heuristics

**Rejected: Bayesian uncertainty (MC Dropout, ensembles).** The standard answer
in ML papers. Problem: it gives you a variance, not a coverage guarantee. "90%
confidence interval" from a Bayesian model is a claim about the model's beliefs,
not a mathematical statement about how often the interval contains the truth.
Conformal gives the latter.

**Rejected: quantile regression.** Predict the 5th and 95th percentile directly.
Problem: quantile losses are notoriously miscalibrated — the empirical coverage
drifts from the nominal level, and you have no finite-sample guarantee. Conformal
coverage is distribution-free and provable.

**Rejected: pure heuristics (fact count + DSTI penalty).** This is what live
routing actually uses today. Problem: it is a guess dressed as a bound. It is
kept only because the conformal engine needs a trained base model and a
calibration set that the pilot does not yet have. The heuristic is explicitly
labeled as a proxy in the code and in LIMITATIONS.md.

**Chosen: Split Conformal Prediction (Vovk et al.).** Train on one set, calibrate
on a second, test on a third. The coverage guarantee is finite-sample and
distribution-free: with alpha=0.10, at least 90% of held-out predictions fall
inside the interval, no matter the underlying distribution. This is the only
uncertainty method that gives you a number you can put in a compliance document
and defend mathematically.

**The honest limitation:** marginal conformal degrades in heteroscedastic tails.
REG-022 measures this: ~70% coverage for high-risk segments (X > 1.0) instead of
the promised 90%. The fix is Mondrian (stratified) conformal, which is in the
ROADMAP. Shipping marginal conformal with a documented degradation is more
honest than shipping a conditional guarantee you have not calibrated yet.

## G5: Fidelity — Why Deterministic Checks, Over LLM-as-Judge

**Rejected: LLM-as-judge.** Use another model to grade the explanation. Problem:
this is the exact failure mode TrustPort exists to prevent. You do not validate a
probabilistic system with another probabilistic system and call it "verification."
An LLM judge can be prompt-injected, can hallucinate, and is non-deterministic —
the same input can get a different grade on Tuesday.

**Rejected: manual review of all explanations.** Correct in principle, impossible
in practice at scale, and the reviewer becomes the bottleneck that the automation
was supposed to remove.

**Chosen: three deterministic checks.** Does the explanation reference the failed
gate? Does it contain PII (regex over emails/phones)? Is it deterministic (same
input, same output)? These are mechanical, auditable, and cannot be gamed. They
do not prove the explanation is *good* — they prove it is *consistent and safe*.
Semantic quality is out of scope for v1.0 and is documented as such.

## Shadow Mode — Why Observational, Over A/B Routing

**Rejected: shadow mode that affects routing.** Run the new policy, log what it
would have decided, but route on the old one. Tempting, but it means the shadow
decision influences nothing and is therefore untestable in production.

**Rejected: true A/B with traffic split.** The industry standard. Problem: in
credit, you cannot randomly deny a customer to "test" a policy. The ethical and
regulatory cost of a real A/B on decisions is prohibitive.

**Chosen: strictly observational shadow.** The shadow fields
(`shadow_outcome`, `shadow_reason_code`) record the decision the shadow policy
would have made, but the primary `outcome` is untouched. This was a real bug in
an earlier commit — shadow mode was converting REFUSED to APPROVED. It was found
by audit, fixed in `acd1b22`, and is now locked by REG-024, which tests all five
outcomes under shadow on and off and asserts they are identical. The lesson is
in the architecture: shadow mode is a *recording* mechanism, never a *decision*
mechanism.

## Audit — Why SQLite WAL + Hash Chain, Over Blockchain, Over Postgres, Over "No Logging"

**Rejected: no logging.** TrustPort returns results, the caller stores them.
Problem: this pushes the auditability burden onto every consumer, and most will
get it wrong. A validation system that cannot prove what it validated is not a
validation system.

**Rejected: blockchain (Hyperledger, a permissioned chain).** Tamper-evident,
distributed, the fashionable answer. Problem: for a single-node pilot, a
blockchain is a distributed database with no distribution and no need for
consensus. The operational overhead (node management, key rotation, chain
reorgs) is pure cost with no benefit at this scale. The hash chain gives 90% of
the tamper-evidence for 1% of the complexity.

**Rejected: Postgres with append-only triggers.** Solid, production-grade.
Problem: it requires a database server, network configuration, and a second
service to operate. For a pilot that must run in `docker compose up` in under
five minutes, SQLite in WAL mode is the right size. The schema is identical to
what Postgres would use, so the migration path is a connection string.

**Chosen: SQLite WAL + chained SHA-256.** Each row contains the hash of the
previous row's payload. `verify_chain()` recomputes every hash and returns False
if any record was altered. WAL mode gives crash durability (the test in REG-025
proves the chain survives a simulated restart). This is not a cryptographic
guarantee against a sophisticated attacker with database access — it is a
tamper-*evidence* mechanism that makes casual alteration detectable. For
production, the same chain wraps an append-only store (S3 Object Lock, Postgres
with row-level security, a ledger database). The architecture does not change;
the storage engine does.

## API — Why FastAPI, Over Flask, Over Django, Over gRPC

**Rejected: Flask.** Minimal, mature. Problem: no automatic OpenAPI, no request
validation (you would re-add Pydantic manually, which is what FastAPI already
does). For a system whose entire value proposition is typed contracts, Flask
means writing the contract layer twice.

**Rejected: Django.** Batteries included, ORM, admin. Problem: TrustPort has no
data model to manage (the audit store is raw SQLite), no admin UI need, and the
full framework is a 5x dependency overhead for three endpoints.

**Rejected: gRPC.** High performance, typed contracts via protobuf. Problem:
the OpenAPI spec that FastAPI generates for free is a major selling point —
non-Python consumers can read `/docs` and integrate in minutes. gRPC requires
protobuf compilation per language and does not give you a browsable spec. For a
pilot meant to be consumed by heterogeneous stacks, REST + OpenAPI wins.

**Chosen: FastAPI.** Pydantic models are already the contracts (G1). FastAPI
reuses them as request/response schemas with zero duplication. The OpenAPI spec
is generated automatically. uvicorn is a single dependency. The cost: FastAPI
pulls in Starlette and a dependency tree that Flask does not have. For three
endpoints, that is acceptable.

## Testing — Why Hypothesis, Over Fuzzing, Over Mutation Testing, Over "More Unit Tests"

**Rejected: more unit tests.** 67 unit/integration/regression tests existed
before Hypothesis. Problem: they test the cases the author thought of. They do
not test the cases the author did not think of. `float('inf')` in G1 was exactly
such a case — found only by property-based generation.

**Rejected: fuzzing (Atheris, boofuzz).** Random input generation. Problem: it
finds crashes, not logic errors. A validator that returns APPROVED for a
malformed proposal does not crash — it silently fails. Fuzzing would not catch
the shadow-mode bug.

**Rejected: mutation testing (mutmut).** Inject bugs, see if tests catch them.
The right idea. Problem: the current mutmut release has a configuration bug on
Python 3.15 (a `TypeError` in its own config loader). Rather than fight a broken
tool, the same goal — proving tests detect real bugs — is achieved more directly
by property-based testing, which generates adversarial inputs against explicit
invariants.

**Chosen: Hypothesis property-based testing.** Four invariants encoded as
properties (REG-026): valid proposals never fail G2, high DSTI is always blocked,
NaN/Inf/negative are always REPAIRED, and the system is deterministic. Hypothesis
generates hundreds of random inputs per property, shrinking failures to minimal
counterexamples. When it found the `inf` bug, it reported the exact input that
broke the invariant. That is the difference between "I tested the cases I knew"
and "I tested the space of cases."

## CI — Why GitHub Actions, Over GitLab CI, Over Jenkins

**Rejected: Jenkins.** Battle-tested, infinitely configurable. Problem: it
requires a server to run, maintain, and secure. For an open-source pilot, the
operational cost of self-hosted CI is pure overhead.

**Rejected: GitLab CI.** Excellent, integrated with GitLab. Problem: the repo is
on GitHub. Moving to GitLab for CI is not justified.

**Chosen: GitHub Actions.** Free for public repos, matrix testing across Python
3.10/3.11/3.12 for free, the badge renders in the README natively. The cost:
Actions YAML is its own dialect and the cache behavior can be surprising. For
this project's scale, the trade is clearly worth it.

## What Was NOT Chosen, and Why It Matters

**No LLM in the loop.** Every decision is deterministic code. The temptation to
use an LLM for G5 (explanation quality) was real and was rejected. The reason is
the manifesto: you cannot validate a probabilistic system with another
probabilistic system.

**No microservices.** The validator is a library, not a service. The API is a
thin wrapper. Splitting into microservices would add network hops, failure modes,
and operational complexity for zero benefit at pilot scale. The monolith is the
right shape.

**No ORM.** The audit store is raw SQL. An ORM (SQLAlchemy) would add a
dependency and an abstraction layer over a single table with a fixed schema.
When the schema grows, the ORM decision revisits.

**No async.** The validator is synchronous CPU-bound work (Z3, arithmetic).
Async would add event-loop complexity for I/O that does not exist. uvicorn runs
sync endpoints in a thread pool, which is correct here.

## The Meta-Principle

Every choice in this document follows one rule: **the simplest mechanism that
provides the required guarantee, with the degradation documented honestly.**

Conformal gives a coverage guarantee; the tail degradation is measured and
documented, not hidden. Z3 gives a formal constraint guarantee; the thread-safety
limitation is locked with a test. SQLite gives durability; the scale limitation is
in the ROADMAP. Pydantic gives type safety; the NaN gap is closed by G1.

A system that promises what it does not deliver is worse than a system that
promises less. The audit trail of this project includes the bugs found (shadow
mode, the inf edge case, the version regex that broke ruff) because a design
philosophy that pretends the path was clean is not a philosophy — it is marketing.

This is the standard TrustPort holds itself to. Every gate, every test, every
line of documentation is written so that a compliance officer, not a fellow
engineer, could read it and know exactly what is proven and what is not.
