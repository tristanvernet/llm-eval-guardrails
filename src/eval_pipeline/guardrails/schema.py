import json
from typing import Any

from pydantic import BaseModel, ValidationError

from eval_pipeline.models.schemas import GuardrailCheckResult, GuardrailStatus


class SchemaConformanceGuardrail:
    """Validates that LLM-generated string responses conform to an expected Pydantic model."""

    def validate(
        self, response_text: str, schema_class: type[BaseModel] | None
    ) -> GuardrailCheckResult:
        """Ensures the text is valid JSON and adheres strictly to the schema."""
        if schema_class is None:
            # If no schema is required for this task, pass automatically
            return GuardrailCheckResult(
                name="Schema Conformance Validator",
                status=GuardrailStatus.PASSED,
                passed=True,
                violations=[],
                details={"schema": None},
            )

        violations: list[str] = []
        details: dict[str, Any] = {"expected_schema": schema_class.__name__}

        # 1. Parse JSON validity
        try:
            # Extract JSON block if wrapped in markdown formatting ```json ... ```
            cleaned_text = response_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text.removeprefix("```json").removesuffix("```").strip()
            elif cleaned_text.startswith("```"):
                cleaned_text = cleaned_text.removeprefix("```").removesuffix("```").strip()

            parsed_json = json.loads(cleaned_text)
        except json.JSONDecodeError as exc:
            violations.append(f"Failed to parse response as valid JSON: {exc.msg}")
            return GuardrailCheckResult(
                name="Schema Conformance Validator",
                status=GuardrailStatus.FAILED,
                passed=False,
                violations=violations,
                details=details,
            )

        # 2. Validate against Pydantic schema
        try:
            schema_class.model_validate(parsed_json)
        except ValidationError as exc:
            for err in exc.errors():
                loc = ".".join(str(p) for p in err["loc"])
                violations.append(f"Schema violation at field '{loc}': {err['msg']}")

        has_violations = len(violations) > 0
        return GuardrailCheckResult(
            name="Schema Conformance Validator",
            status=GuardrailStatus.FAILED if has_violations else GuardrailStatus.PASSED,
            passed=not has_violations,
            violations=violations,
            details=details,
        )
