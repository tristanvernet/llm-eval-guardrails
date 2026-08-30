import re

from eval_pipeline.config.settings import settings
from eval_pipeline.evaluators.base import BaseEvaluator
from eval_pipeline.models.schemas import GoldenTestCase, LLMOutput, MetricScore, MetricType


class ContextPrecisionEvaluator(BaseEvaluator):
    """
    Evaluates whether retrieved context chunks contain relevant information
    relative to the expected ground-truth target.
    """

    def __init__(self, threshold: float | None = None) -> None:
        super().__init__(
            metric_type=MetricType.CONTEXT_PRECISION,
            threshold=threshold if threshold is not None else settings.min_context_precision_score,
        )

    async def evaluate(self, test_case: GoldenTestCase, output: LLMOutput) -> MetricScore:
        if not test_case.retrieved_contexts:
            return MetricScore(
                metric=self.metric_type,
                score=1.0,
                passed=True,
                threshold=self.threshold,
                reasoning="No context chunks in test case; context precision check skipped.",
            )

        target_reference = test_case.expected_output or test_case.input_prompt
        target_terms = set(re.findall(r"\b\w{4,}\b", target_reference.lower()))

        if not target_terms:
            return MetricScore(
                metric=self.metric_type,
                score=1.0,
                passed=True,
                threshold=self.threshold,
                reasoning="No target terms available for context precision comparison.",
            )

        relevant_chunks = 0
        for chunk in test_case.retrieved_contexts:
            chunk_lower = chunk.lower()
            matched = sum(1 for term in target_terms if term in chunk_lower)
            if matched >= 1:
                relevant_chunks += 1

        precision_score = relevant_chunks / len(test_case.retrieved_contexts)
        passed = precision_score >= self.threshold

        reasoning = (
            f"Context precision: {relevant_chunks}/{len(test_case.retrieved_contexts)} "
            f"retrieved chunks contained target facts."
        )

        return MetricScore(
            metric=self.metric_type,
            score=round(precision_score, 3),
            passed=passed,
            threshold=self.threshold,
            reasoning=reasoning,
        )
