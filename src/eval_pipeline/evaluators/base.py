from abc import ABC, abstractmethod

from eval_pipeline.models.schemas import GoldenTestCase, LLMOutput, MetricScore, MetricType


class BaseEvaluator(ABC):
    """Abstract base class for all LLM evaluation metrics."""

    def __init__(self, metric_type: MetricType, threshold: float) -> None:
        self.metric_type = metric_type
        self.threshold = threshold

    @abstractmethod
    async def evaluate(self, test_case: GoldenTestCase, output: LLMOutput) -> MetricScore:
        """Computes metric score and reasoning trace for a test case."""
