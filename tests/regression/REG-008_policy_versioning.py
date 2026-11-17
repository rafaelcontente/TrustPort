import copy
import json

from trust_net_port.schema.contracts import AgentProposal, OutcomeEnum
from trust_net_port.validator import PortValidator


def test_policy_version_is_attached_to_result():
    validator = PortValidator()
    proposal = AgentProposal(
        proposal_id="P-POL-01",
        case_id="C-POL-01",
        action="approve",
        amount=10000.0,
        term_months=12,
        dsti_ratio=0.30,
        facts_cited=["F-1", "F-2", "F-3"],
    )
    result = validator.validate(proposal)
    assert result.policy_version == "1.0.0"


def test_policy_change_affects_outcome():
    validator = PortValidator()
    proposal = AgentProposal(
        proposal_id="P-POL-02",
        case_id="C-POL-02",
        action="approve",
        amount=10000.0,
        term_months=12,
        dsti_ratio=0.35,
        facts_cited=["F-1", "F-2", "F-3"],
    )

    # 1. Verificar que passa com a política atual (DSTI 35% < 40%)
    assert validator.validate(proposal).outcome == OutcomeEnum.APPROVED

    # 2. Mudar temporariamente a política para limite mais restrito (30%)
    policy_path = validator.policy_path
    original_policy = json.loads(policy_path.read_text())
    # Deepcopy para não mutar o original via referência partilhada
    stricter_policy = copy.deepcopy(original_policy)
    stricter_policy["rules"]["max_dsti_ratio"] = 0.30
    policy_path.write_text(json.dumps(stricter_policy))

    try:
        new_validator = PortValidator()
        result = new_validator.validate(proposal)

        # 3. Agora deve falhar no G2
        assert result.outcome == OutcomeEnum.REFUSED
        assert result.reason_code == "RUL-01"
    finally:
        # Restaurar política original (agora sim, o original intacto)
        policy_path.write_text(json.dumps(original_policy))
