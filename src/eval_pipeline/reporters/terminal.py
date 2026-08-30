from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from eval_pipeline.models.schemas import EvaluationSuiteReport

console = Console()


def print_evaluation_summary(report: EvaluationSuiteReport) -> None:
    """Prints a styled Rich console summary of evaluation metrics and guardrail status."""
    title_color = "green" if report.all_passed else "red"
    status_text = "PASSED" if report.all_passed else "FAILED"

    console.print(
        Panel(
            f"[bold {title_color}]Evaluation Suite: {report.suite_name} - {status_text}[/bold {title_color}]\n"
            f"Total Tests: {report.total_tests} | Passed: {report.passed_tests} | "
            f"Failed: {report.failed_tests} | Violations: {report.guardrail_violation_count}\n"
            f"Duration: {report.duration_seconds:.2f}s",
            title="LLM Quality & Guardrails Gate",
            border_style=title_color,
        )
    )

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Test ID", width=14)
    table.add_column("Guardrails", justify="center")
    table.add_column("Faithfulness", justify="right")
    table.add_column("Relevance", justify="right")
    table.add_column("Precision", justify="right")
    table.add_column("Verdict", justify="center")

    for res in report.results:
        guard_passed = all(g.passed for g in res.guardrail_results)
        guard_badge = "[green]PASS[/green]" if guard_passed else "[red]FAIL[/red]"

        # Extract metric scores safely
        scores = {m.metric.value: m.score for m in res.metric_scores}
        f_score = f"{scores.get('FAITHFULNESS', 1.0):.2f}"
        r_score = f"{scores.get('ANSWER_RELEVANCE', 1.0):.2f}"
        p_score = f"{scores.get('CONTEXT_PRECISION', 1.0):.2f}"

        verdict = (
            "[bold green]PASS[/bold green]" if res.overall_passed else "[bold red]FAIL[/bold red]"
        )
        table.add_row(res.test_case_id, guard_badge, f_score, r_score, p_score, verdict)

    console.print(table)
