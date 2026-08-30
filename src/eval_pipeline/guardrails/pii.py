import re
from typing import Any

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

from eval_pipeline.models.schemas import GuardrailCheckResult, GuardrailStatus


class PIIGuardrail:
    """Detects and redacts Personally Identifiable Information (PII) using Presidio & Regex."""

    def __init__(self, blocked_entities: list[str] | None = None) -> None:
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        self.blocked_entities = blocked_entities or [
            "EMAIL_ADDRESS",
            "PHONE_NUMBER",
            "US_SSN",
            "CREDIT_CARD",
            "US_PASSPORT",
            "IP_ADDRESS",
        ]
        # Custom regex patterns for secrets and API keys
        self.secret_patterns: dict[str, re.Pattern[str]] = {
            "OPENAI_API_KEY": re.compile(r"sk-[a-zA-Z0-9]{32,}", re.IGNORECASE),
            "GENERIC_SECRET_TOKEN": re.compile(
                r"(?i)(api[_-]?key|secret|token|bearer)\s*[:=]\s*['\"]?[a-zA-Z0-9_\-]{16,}['\"]?"
            ),
        }

    def scan(self, text: str) -> GuardrailCheckResult:
        """Analyzes text for PII entities and secret tokens."""
        violations: list[str] = []
        details: dict[str, Any] = {"detected_entities": []}

        # 1. Presidio NER analysis
        results = self.analyzer.analyze(
            text=text,
            entities=self.blocked_entities,
            language="en",
        )

        for res in results:
            detected_type = res.entity_type
            entity_val = text[res.start : res.end]
            violations.append(f"PII Entity '{detected_type}' detected (score: {res.score:.2f})")
            details["detected_entities"].append(
                {"type": detected_type, "score": res.score, "value_masked": f"{entity_val[:2]}***"}
            )

        # 2. Regex Secret Scanning
        for secret_name, pattern in self.secret_patterns.items():
            if pattern.search(text):
                violations.append(f"Hardcoded secret token matched pattern: {secret_name}")
                details["detected_entities"].append({"type": secret_name, "score": 1.0})

        has_violations = len(violations) > 0
        return GuardrailCheckResult(
            name="PII & Secret Scanner",
            status=GuardrailStatus.FAILED if has_violations else GuardrailStatus.PASSED,
            passed=not has_violations,
            violations=violations,
            details=details,
        )

    def redact(self, text: str) -> str:
        """Redacts detected PII entities with generic placeholder tokens."""
        results = self.analyzer.analyze(
            text=text,
            entities=self.blocked_entities,
            language="en",
        )
        anonymized = self.anonymizer.anonymize(text=text, analyzer_results=results)
        return str(anonymized.text)
