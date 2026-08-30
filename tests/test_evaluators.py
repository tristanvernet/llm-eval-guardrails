import pytest

from eval_pipeline.core.runner import EvaluationRunner
from eval_pipeline.evaluators.faithfulness import FaithfulnessEvaluator
from eval_pipeline.evaluators.relevance import AnswerRelevanceEvaluator
from eval_pipeline.models.schemas import GoldenTestCase, LLMOutput


@pytest.mark.asyncio
async def test_faithfulness_evaluator_catches_hallucination() -> None:
    evaluator = FaithfulnessEvaluator(threshold=0.85)

    test_case = GoldenTestCase(
        input_prompt="What are the store hours?",
        retrieved_contexts=["Our store is open Monday to Friday from 9 AM to 5 PM."],
    )

    # Grounded response
    grounded_output = LLMOutput(
        response_text="The store is open from Monday to Friday, 9 AM to 5 PM."
    )
    score_grounded = await evaluator.evaluate(test_case, grounded_output)
    assert score_grounded.passed is True
    assert score_grounded.score >= 0.85

    # Hallucinated response
    hallucinated_output = LLMOutput(
        response_text="The store operates 24 hours a day on weekends and holidays."
    )
    score_hallucinated = await evaluator.evaluate(test_case, hallucinated_output)
    assert score_hallucinated.passed is False
    assert score_hallucinated.score < 0.85


@pytest.mark.asyncio
async def test_relevance_evaluator_keyword_matching() -> None:
    evaluator = AnswerRelevanceEvaluator(threshold=0.75)

    test_case = GoldenTestCase(
        input_prompt="How do I configure Redis connection timeouts?",
        retrieved_contexts=[],
    )

    relevant_output = LLMOutput(
        response_text="To configure Redis connection timeouts, adjust the timeout settings in the config."
    )
    irrelevant_output = LLMOutput(
        response_text="Baking a chocolate cake requires sugar, cocoa, and flour."
    )

    score_rel = await evaluator.evaluate(test_case, relevant_output)
    assert score_rel.passed is True

    score_irrel = await evaluator.evaluate(test_case, irrelevant_output)
    assert score_irrel.passed is False


@pytest.mark.asyncio
async def test_end_to_end_runner_suite() -> None:
    runner = EvaluationRunner()

    test_cases = [
        GoldenTestCase(
            id="tc-1",
            input_prompt="What is Python?",
            retrieved_contexts=[
                "Python is a high-level programming language created by Guido van Rossum."
            ],
            expected_output="Python is a high-level language created by Guido van Rossum.",
        )
    ]

    outputs = [
        LLMOutput(
            response_text="Python is a high-level programming language created by Guido van Rossum."
        )
    ]

    report = await runner.run_suite("Test Suite 1", test_cases, outputs)
    assert report.total_tests == 1
    assert report.passed_tests == 1
    assert report.all_passed is True
    assert report.guardrail_violation_count == 0
