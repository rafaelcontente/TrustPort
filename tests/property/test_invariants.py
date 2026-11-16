"""Property-based testing with Hypothesis to prove system invariants."""

from hypothesis import given, settings
from hypothesis import strategies as st

from trust_net_port.schema.contracts import AgentProposal, OutcomeEnum
from trust_net_port.validator import PortValidator

# Instância module-level é segura aqui pois o validador é stateless para estas validações
validator = PortValidator()

# Estratégias de dados para gerar propostas aleatórias
valid_facts = st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=20)
valid_amounts = st.floats(min_value=1.0, max_value=999999.0, allow_nan=False, allow_infinity=False)
valid_terms = st.integers(min_value=6, max_value=120)
valid_dsti = st.floats(min_value=0.1, max_value=39.9, allow_nan=False, allow_infinity=False)

invalid_amounts = st.one_of(
    st.floats(min_value=-1000.0, max_value=0.0, allow_nan=False, allow_infinity=False),
    st.just(float('nan')),
    st.just(float('inf'))
)


# INVARIANTE 1: Qualquer proposta com parâmetros válidos e DSTI < 40% não deve falhar no G2
@given(
    amount=valid_amounts,
    term=valid_terms,
    dsti=valid_dsti,
    facts=valid_facts
)
@settings(max_examples=200)
def test_invariant_valid_proposal_never_refused_by_rules(amount, term, dsti, facts):
    proposal = AgentProposal(
        proposal_id="P-PBT-01", case_id="C-PBT-01", action="approve",
        amount=amount, term_months=term, dsti_ratio=dsti, facts_cited=facts
    )
    result = validator.validate(proposal)
    assert "G2_RULES" not in result.gates_failed, f"Valid DSTI {dsti} was refused by G2"


# INVARIANTE 2: Qualquer proposta com DSTI > 40.0 deve ser REFUSED (ou REPAIRED se falhar G1)
@given(
    amount=valid_amounts,
    term=valid_terms,
    dsti=st.floats(min_value=40.1, max_value=100.0, allow_nan=False, allow_infinity=False),
    facts=valid_facts
)
@settings(max_examples=200)
def test_invariant_high_dsti_always_fails(amount, term, dsti, facts):
    proposal = AgentProposal(
        proposal_id="P-PBT-02", case_id="C-PBT-02", action="approve",
        amount=amount, term_months=term, dsti_ratio=dsti, facts_cited=facts
    )
    result = validator.validate(proposal)
    assert result.outcome in (OutcomeEnum.REPAIRED, OutcomeEnum.REFUSED), f"DSTI {dsti} was not blocked"
    assert "G2_RULES" in result.gates_failed or "G1_SCHEMA" in result.gates_failed


# INVARIANTE 3: Edge cases de G1 (NaN, Inf, zero, negativo) são sempre REPAIRED
@given(
    amount=invalid_amounts,
    term=valid_terms,
    dsti=valid_dsti,
    facts=valid_facts
)
@settings(max_examples=100)
def test_invariant_invalid_amount_always_repaired(amount, term, dsti, facts):
    proposal = AgentProposal(
        proposal_id="P-PBT-03", case_id="C-PBT-03", action="approve",
        amount=amount, term_months=term, dsti_ratio=dsti, facts_cited=facts
    )
    result = validator.validate(proposal)
    assert result.outcome == OutcomeEnum.REPAIRED
    assert "G1_SCHEMA" in result.gates_failed


# INVARIANTE 4: Determinismo sob inputs idênticos
@given(
    amount=valid_amounts,
    term=valid_terms,
    dsti=valid_dsti,
    facts=valid_facts
)
@settings(max_examples=50)
def test_invariant_determinism(amount, term, dsti, facts):
    proposal = AgentProposal(
        proposal_id="P-PBT-04", case_id="C-PBT-04", action="approve",
        amount=amount, term_months=term, dsti_ratio=dsti, facts_cited=facts,
        correlation_id="fixed-seed-test"
    )
    r1 = validator.validate(proposal)
    r2 = validator.validate(proposal)
    
    assert r1.outcome == r2.outcome
    assert r1.reason_code == r2.reason_code
    assert r1.gates_passed == r2.gates_passed
    assert r1.gates_failed == r2.gates_failed
