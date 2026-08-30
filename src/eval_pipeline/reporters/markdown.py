from eval_pipeline.models.schemas import EvaluationSuiteReport


def generate_markdown_pr_report(report: EvaluationSuiteReport) -> str:
    """Formats an evaluation report into markdown for automated GitHub PR comments."""
    badge = "✅ **PASSED**" if report.all_passed else "❌ **FAILED (BLOCKED)**"

    lines: list[str] = [
        "## 🤖 Automated LLM Evaluation & Guardrails CI Report",
        f"**Verdict:** {badge}",
        "",
        "| Metric | Summary Value |",
        "| :--- | :--- |",
        f"| **Total Test Cases** | `{report.total_tests}` |",
        f"| **Passed Tests** | `{report.passed_tests}` |",
        f"| **Failed Tests** | `{report.failed_tests}` |",
        f"| **Guardrail Violations** | `{report.guardrail_violation_count}` |",
        f"| **Test Execution Time** | `{report.duration_seconds:.2f}s` |",
        "",
        "### 📊 Detailed Test Breakdown",
        "",
        "| Test ID | Guardrails | Faithfulness | Relevance | Context Precision | Result |",
        "| :--- | :---: | :---: | :---: | :---: | :---: |",
    ]

    for res in report.results:
        guard_passed = all(g.passed for g in res.guardrail_results)
        guard_str = "✅ PASS" if guard_passed else "❌ FAIL"
        scores = {m.metric.value: m.score for m in res.metric_scores}
        f_score = f"{scores.get('FAITHFULNESS', 1.0):.2f}"
        r_score = f"{scores.get('ANSWER_RELEVANCE', 1.0):.2f}"
        p_score = f"{scores.get('CONTEXT_PRECISION', 1.0):.2f}"
        res_str = "✅ PASS" if res.overall_passed else "❌ FAIL"

        lines.append(
            f"| `{res.test_case_id}` | {guard_str} | {f_score} | {r_score} | {p_score} | {res_str} |"
        )

    lines.append("")
    lines.append("> _Report generated automatically by LLM Evaluation & Guardrails CI Action._")
    return "\n".join(lines)
