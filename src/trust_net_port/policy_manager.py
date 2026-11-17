"""Dynamic Policy Manager for TrustPort."""

from pathlib import Path

import yaml


class PolicyManager:
    def __init__(self, policy_path: str = "src/trust_net_port/policy.yaml"):
        self.policy_path = Path(policy_path)
        self._policy: dict = {}
        self.reload()

    def reload(self) -> dict:
        """Reloads the policy from the YAML file."""
        with open(self.policy_path, "r") as f:
            self._policy = yaml.safe_load(f).get("rules", {})
        return self._policy

    def get(self, key: str, default=None):
        return self._policy.get(key, default)


# Global instance
policy = PolicyManager()
