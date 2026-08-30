import re

from eval_pipeline.config.settings import settings
from eval_pipeline.evaluators.base import BaseEvaluator
from eval_pipeline.models.schemas import GoldenTestCase, LLMOutput, MetricScore, MetricType


class FaithfulnessEvaluator(BaseEvaluator):
    """
    Measures factual consistency of generated response against provided context.
    Detects hallucinations by verifying claims against retrieved context chunks.
    """

    def __init__(self, threshold: float | None = None) -> None:
        super().__init__(
            metric_type=MetricType.FAITHFULNESS,
            threshold=threshold if threshold is not None else settings.min_faithfulness_score,
        )

    async def evaluate(self, test_case: GoldenTestCase, output: LLMOutput) -> MetricScore:
        if not test_case.retrieved_contexts:
            # If no context was provided, faithfulness against context cannot be evaluated
            return MetricScore(
                metric=self.metric_type,
                score=1.0,
                passed=True,
                threshold=self.threshold,
                reasoning="No context chunks provided for verification; skipped hallucination check.",
            )

        full_context = " ".join(test_case.retrieved_contexts).lower()
        response_text = output.response_text.strip()

        # Split response into individual factual sentences/statements
        sentences = [s.strip() for s in re.split(r"[.!?]+", response_text) if len(s.strip()) > 5]

        if not sentences:
            return MetricScore(
                metric=self.metric_type,
                score=0.0,
                passed=False,
                threshold=self.threshold,
                reasoning="Empty or unparseable response text.",
            )

        supported_claims = 0
        unsupported_claims: list[str] = []

        for sentence in sentences:
            # Extract key words (ignoring short stopwords) to verify grounding
            keywords = [w.lower() for w in re.findall(r"\b\w{4,}\b", sentence)]
            if not keywords:
                supported_claims += 1
                continue

            # Check what percentage of key terms appear in retrieved context
            matched_terms = [kw for kw in keywords if kw in full_context]
            grounding_ratio = len(matched_terms) / len(keywords)

            # A statement is grounded if >= 60% of its content terms exist in context
            if grounding_ratio >= 0.60:
                supported_claims += 1
            else:
                unsupported_claims.append(sentence)

        faithfulness_score = supported_claims / len(sentences)
        passed = faithfulness_score >= self.threshold

        if passed:
            reasoning = f"Faithful: {supported_claims}/{len(sentences)} statements grounded in retrieved context."
        else:
            reasoning = (
                f"Hallucination detected ({faithfulness_score:.2f} < {self.threshold:.2f}). "
                f"Unsupported statements: {'; '.join(unsupported_claims[:2])}"
            )

        return MetricScore(
            metric=self.metric_type,
            score=round(faithfulness_score, 3),
            passed=passed,
            threshold=self.threshold,
            reasoning=reasoning,
        )
