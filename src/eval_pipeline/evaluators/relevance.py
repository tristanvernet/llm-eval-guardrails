import re

from eval_pipeline.config.settings import settings
from eval_pipeline.evaluators.base import BaseEvaluator
from eval_pipeline.models.schemas import GoldenTestCase, LLMOutput, MetricScore, MetricType

STOP_WORDS = {
    "what",
    "when",
    "where",
    "which",
    "who",
    "whom",
    "whose",
    "why",
    "how",
    "does",
    "explain",
    "tell",
    "describe",
    "about",
    "this",
    "that",
    "these",
    "those",
    "have",
    "from",
    "with",
    "your",
    "please",
    "the",
    "for",
    "are",
    "and",
    "can",
    "could",
    "would",
    "should",
}


class AnswerRelevanceEvaluator(BaseEvaluator):
    """Measures how directly the LLM output addresses the topical keywords in the input prompt."""

    def __init__(self, threshold: float | None = None) -> None:
        super().__init__(
            metric_type=MetricType.ANSWER_RELEVANCE,
            threshold=threshold if threshold is not None else settings.min_relevance_score,
        )

    async def evaluate(self, test_case: GoldenTestCase, output: LLMOutput) -> MetricScore:
        all_words = re.findall(r"\b\w{3,}\b", test_case.input_prompt.lower())
        prompt_keywords = {w for w in all_words if w not in STOP_WORDS}
        response_text = output.response_text.lower()

        if not prompt_keywords:
            return MetricScore(
                metric=self.metric_type,
                score=1.0,
                passed=True,
                threshold=self.threshold,
                reasoning="Prompt contains no distinct topical keywords.",
            )

        matched_keywords = [kw for kw in prompt_keywords if kw in response_text]
        relevance_score = len(matched_keywords) / len(prompt_keywords)
        passed = relevance_score >= self.threshold

        reasoning = (
            f"Prompt topical keyword coverage: {len(matched_keywords)}/{len(prompt_keywords)} "
            f"({relevance_score * 100:.1f}% matched)."
        )

        return MetricScore(
            metric=self.metric_type,
            score=round(relevance_score, 3),
            passed=passed,
            threshold=self.threshold,
            reasoning=reasoning,
        )
