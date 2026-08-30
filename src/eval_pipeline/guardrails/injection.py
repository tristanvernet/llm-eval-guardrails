import re
from typing import Any

from eval_pipeline.models.schemas import GuardrailCheckResult, GuardrailStatus


class PromptInjectionGuardrail:
    """Scans inputs for adversarial prompt injections, jailbreaks, and system prompt leaks."""

    INJECTION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
        (
            "System Override Attempt",
            re.compile(
                r"(?i)(ignore\s+all\s+(prior|previous)\s+instructions|disregard\s+all\s+rules)",
            ),
        ),
        (
            "Roleplay Jailbreak Signature",
            re.compile(
                r"(?i)(you\s+are\s+now\s+in\s+developer\s+mode|dan\s+mode|always\s+say\s+yes|do\s+anything\s+now)",
            ),
        ),
        (
            "System Prompt Exfiltration",
            re.compile(
                r"(?i)(repeat\s+the\s+system\s+prompt|print\s+your\s+initial\s+instructions|output\s+above\s+text)",
            ),
        ),
        (
            "Delimiter Collision Injection",
            re.compile(r"(?i)(```markdown|<system_prompt>|\[INST\]|<<SYS>>)", re.DOTALL),
        ),
    ]

    def scan(self, text: str) -> GuardrailCheckResult:
        """Evaluates input string for adversarial jailbreaks or overrides."""
        violations: list[str] = []
        details: dict[str, Any] = {"matched_rules": []}

        for rule_name, pattern in self.INJECTION_PATTERNS:
            match = pattern.search(text)
            if match:
                snippet = match.group(0)[:60]
                violations.append(f"Adversarial signature detected: '{rule_name}' ('{snippet}')")
                details["matched_rules"].append(rule_name)

        has_violations = len(violations) > 0
        return GuardrailCheckResult(
            name="Prompt Injection & Jailbreak Guard",
            status=GuardrailStatus.FAILED if has_violations else GuardrailStatus.PASSED,
            passed=not has_violations,
            violations=violations,
            details=details,
        )
