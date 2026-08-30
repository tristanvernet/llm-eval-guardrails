import asyncio
import sys

from eval_pipeline.config.settings import settings
from eval_pipeline.core.runner import EvaluationRunner
from eval_pipeline.models.schemas import GoldenTestCase, LLMOutput
from eval_pipeline.reporters.markdown import generate_markdown_pr_report
from eval_pipeline.reporters.terminal import print_evaluation_summary


async def run_cli() -> int:
    """CLI test runner entrypoint executed during CI runs."""
    # Synthetic golden test cases simulating RAG pipeline outputs
    test_cases = [
        GoldenTestCase(
            id="test-rag-01",
            input_prompt="What is the refund policy for annual enterprise subscriptions?",
            retrieved_contexts=[
                "Enterprise annual subscriptions are eligible for a prorated refund within 30 days of renewal."
            ],
            expected_output="Enterprise subscriptions offer a prorated refund within 30 days of renewal.",
        ),
        GoldenTestCase(
            id="test-rag-02",
            input_prompt="How do I reset my API secret keys in the dashboard?",
            retrieved_contexts=[
                "To regenerate secret keys, navigate to Dashboard > Settings > API Keys and select Revoke & Regenerate."
            ],
            expected_output="Go to Dashboard > Settings > API Keys and click Revoke & Regenerate.",
        ),
    ]

    # Candidate outputs produced by LLM
    outputs = [
        LLMOutput(
            response_text="Annual enterprise subscriptions can receive a prorated refund within 30 days of renewal."
        ),
        LLMOutput(
            response_text="Navigate to Dashboard > Settings > API Keys and click Revoke & Regenerate to reset your secret keys."
        ),
    ]

    runner = EvaluationRunner()
    report = await runner.run_suite("PR Quality Gate Suite", test_cases, outputs)

    # Print Rich terminal table
    print_evaluation_summary(report)

    # Export markdown report for GitHub PR Actions
    reports_dir = settings.reports_dir
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_file = reports_dir / "eval_report.md"
    report_file.write_text(generate_markdown_pr_report(report), encoding="utf-8")

    return 0 if report.all_passed else 1


def main() -> None:
    exit_code = asyncio.run(run_cli())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
