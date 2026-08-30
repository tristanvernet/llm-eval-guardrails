import time
import uuid
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class GuardrailStatus(StrEnum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    WARNED = "WARNED"


class MetricType(StrEnum):
    FAITHFULNESS = "FAITHFULNESS"
    ANSWER_RELEVANCE = "ANSWER_RELEVANCE"
    CONTEXT_PRECISION = "CONTEXT_PRECISION"
    SEMANTIC_SIMILARITY = "SEMANTIC_SIMILARITY"
    CUSTOM_RUBRIC = "CUSTOM_RUBRIC"


class GoldenTestCase(BaseModel):
    """Represents a single deterministic reference test item in a golden dataset."""

    id: str = Field(default_factory=lambda: f"test-{uuid.uuid4().hex[:8]}")
    input_prompt: str = Field(..., description="The user prompt or query submitted to the LLM.")
    retrieved_contexts: list[str] = Field(
        default_factory=list,
        description="Retrieved reference context chunks provided to the LLM.",
    )
    expected_output: str | None = Field(
        default=None,
        description="The ground-truth or ideal reference answer.",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class LLMOutput(BaseModel):
    """Encapsulates the response produced by the candidate LLM or chain."""

    response_text: str = Field(..., description="The generated string or JSON output.")
    latency_seconds: float = Field(0.0, ge=0.0)
    token_count: int = Field(0, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GuardrailCheckResult(BaseModel):
    """Individual result for a specific safety or compliance check."""

    name: str = Field(..., description="Name of the guardrail (e.g., PII, Injection, Schema).")
    status: GuardrailStatus
    passed: bool
    violations: list[str] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)


class MetricScore(BaseModel):
    """Calculated metric score with reasoning trace."""

    metric: MetricType
    score: float = Field(..., ge=0.0, le=1.0, description="Normalized score between 0.0 and 1.0.")
    passed: bool
    threshold: float
    reasoning: str = Field(..., description="Chain-of-thought justification for the score.")


class SingleEvalResult(BaseModel):
    """Complete evaluation report for a single test case."""

    test_case_id: str
    prompt: str
    response: str
    guardrail_results: list[GuardrailCheckResult] = Field(default_factory=list)
    metric_scores: list[MetricScore] = Field(default_factory=list)
    overall_passed: bool = True
    executed_at: float = Field(default_factory=time.time)


class EvaluationSuiteReport(BaseModel):
    """Aggregated report summarizing an entire evaluation run across all test cases."""

    suite_name: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    average_scores: dict[str, float] = Field(default_factory=dict)
    guardrail_violation_count: int = 0
    all_passed: bool
    results: list[SingleEvalResult] = Field(default_factory=list)
    duration_seconds: float = 0.0
