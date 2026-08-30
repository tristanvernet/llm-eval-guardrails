import time

from pydantic import BaseModel

from eval_pipeline.evaluators.base import BaseEvaluator
from eval_pipeline.evaluators.context_precision import ContextPrecisionEvaluator
from eval_pipeline.evaluators.faithfulness import FaithfulnessEvaluator
from eval_pipeline.evaluators.relevance import AnswerRelevanceEvaluator
from eval_pipeline.guardrails.injection import PromptInjectionGuardrail
from eval_pipeline.guardrails.pii import PIIGuardrail
from eval_pipeline.guardrails.schema import SchemaConformanceGuardrail
from eval_pipeline.models.schemas import (
    EvaluationSuiteReport,
    GoldenTestCase,
    GuardrailCheckResult,
    LLMOutput,
    SingleEvalResult,
)


class EvaluationRunner:
    """Orchestrates multi-phase evaluation: Guardrails pre-flight -> LLM evaluation metrics."""

    def __init__(
        self,
        evaluators: list[BaseEvaluator] | None = None,
        schema_class: type[BaseModel] | None = None,
    ) -> None:
        self.pii_guardrail = PIIGuardrail()
        self.injection_guardrail = PromptInjectionGuardrail()
        self.schema_guardrail = SchemaConformanceGuardrail()
        self.schema_class = schema_class

        self.evaluators = evaluators or [
            FaithfulnessEvaluator(),
            AnswerRelevanceEvaluator(),
            ContextPrecisionEvaluator(),
        ]

    async def evaluate_single(
        self,
        test_case: GoldenTestCase,
        output: LLMOutput,
    ) -> SingleEvalResult:
        """Executes guardrails and evaluators on a single test item."""
        guardrail_results: list[GuardrailCheckResult] = []

        # 1. Guardrail checks on input prompt and model response
        guardrail_results.append(self.injection_guardrail.scan(test_case.input_prompt))
        guardrail_results.append(self.pii_guardrail.scan(output.response_text))
        guardrail_results.append(
            self.schema_guardrail.validate(output.response_text, self.schema_class)
        )

        all_guardrails_passed = all(g.passed for g in guardrail_results)

        # 2. Metric evaluation (faithfulness, relevance, precision)
        metric_scores = []
        for evaluator in self.evaluators:
            score = await evaluator.evaluate(test_case, output)
            metric_scores.append(score)

        all_metrics_passed = all(m.passed for m in metric_scores)
        overall_passed = all_guardrails_passed and all_metrics_passed

        return SingleEvalResult(
            test_case_id=test_case.id,
            prompt=test_case.input_prompt,
            response=output.response_text,
            guardrail_results=guardrail_results,
            metric_scores=metric_scores,
            overall_passed=overall_passed,
        )

    async def run_suite(
        self,
        suite_name: str,
        test_cases: list[GoldenTestCase],
        outputs: list[LLMOutput],
    ) -> EvaluationSuiteReport:
        """Runs the entire test suite and aggregates scores into an EvaluationSuiteReport."""
        start_time = time.time()
        results: list[SingleEvalResult] = []
        guardrail_violations = 0

        for tc, out in zip(test_cases, outputs, strict=True):
            result = await self.evaluate_single(tc, out)
            results.append(result)
            guardrail_violations += sum(1 for g in result.guardrail_results if not g.passed)

        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.overall_passed)
        failed_tests = total_tests - passed_tests
        duration = time.time() - start_time

        # Calculate metric averages
        avg_scores: dict[str, float] = {}
        for evaluator in self.evaluators:
            metric_name = evaluator.metric_type.value
            scores = [
                m.score for r in results for m in r.metric_scores if m.metric.value == metric_name
            ]
            if scores:
                avg_scores[metric_name] = round(sum(scores) / len(scores), 3)

        return EvaluationSuiteReport(
            suite_name=suite_name,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            average_scores=avg_scores,
            guardrail_violation_count=guardrail_violations,
            all_passed=(failed_tests == 0),
            results=results,
            duration_seconds=round(duration, 3),
        )
