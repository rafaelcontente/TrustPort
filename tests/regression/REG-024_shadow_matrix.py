import pytest

from trust_net_port.schema.contracts import AgentProposal, OutcomeEnum
from trust_net_port.validator import PortValidator

CASES = [
    ("g1_repaired", -1.0, 12, 0.30, ["F1"], OutcomeEnum.REPAIRED),
    ("g2_refused", 10000.0, 12, 0.50, ["F1", "F2", "F3"], OutcomeEnum.REFUSED),
    ("g3_refused", 60000.0, 12, 0.30, ["F1", "F2", "F3"], OutcomeEnum.REFUSED),
    ("g4_escalated", 10000.0, 12, 0.30, ["F1"], OutcomeEnum.ESCALATED),
    ("approved", 10000.0, 12, 0.30, ["F1", "F2", "F3"], OutcomeEnum.APPROVED),
]


def _make(name, amount, term, dsti, facts):
    return AgentProposal(
        proposal_id=f"P-{name}",
        case_id=f"C-{name}",
        action="approve",
        amount=amount,
        term_months=term,
        dsti_ratio=dsti,
        facts_cited=facts,
    )


@pytest.mark.parametrize(("name", "amount", "term", "dsti", "facts", "expected"), CASES)
def test_shadow_mode_never_changes_any_outcome(name, amount, term, dsti, facts, expected):
    v_off = PortValidator()
    r_off = v_off.validate(_make(name, amount, term, dsti, facts))
    assert r_off.outcome == expected

    v_on = PortValidator()
    v_on.set_shadow_mode(True)
    r_on = v_on.validate(_make(name, amount, term, dsti, facts))

    assert r_on.outcome == r_off.outcome, f"shadow mode altered outcome in {name}"
    assert r_on.reason_code == r_off.reason_code, f"shadow mode altered reason_code in {name}"
    assert r_on.shadow_outcome == r_off.outcome.value
    assert r_on.shadow_reason_code == r_off.reason_code
