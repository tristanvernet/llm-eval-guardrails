# Automated LLM Evaluation & Guardrails CI Pipeline

An enterprise-grade quality assurance, safety guardrails, and automated evaluation harness for LLM chains and Retrieval-Augmented Generation (RAG) systems built with **Python 3.12**, **Pydantic v2**, and **Microsoft Presidio**, integrated into **GitHub Actions CI**.

---

## Overview

Prompt changes, retrieval configurations, and model updates introduce non-deterministic behavior that standard unit tests cannot reliably catch. This pipeline acts as a zero-regression CI/CD gate:

1. **Pre-Flight Safety Guardrails:** Deterministic scans for PII leaks, adversarial prompt injections, and JSON schema non-conformance.
2. **LLM-as-a-Judge Evaluation Engine:** Quantifies semantic quality (Faithfulness, Answer Relevance, Context Precision) on a normalized [0.0, 1.0] scale with reasoning traces.
3. **CI/CD Quality Gate:** Halts pull requests that fail minimum quality thresholds (< 0.85) or trigger safety violations, automatically posting detailed Markdown reports to the PR thread.

---

## Architecture

```text
       [ Pull Request / Prompt / Chain Change ]
                          │
                          ▼
            [ GitHub Actions CI Runner ]
                          │
    ┌─────────────────────┴─────────────────────────┐
    │                                               │
    ▼                                               ▼
[ Stage 1: Safety Guardrails ]            [ Stage 2: LLM Eval Engine ]
  • Presidio PII & Secret Scanner           • Faithfulness & Hallucination
  • Adversarial Injection Shield            • Context Relevance & Precision
  • Strict Pydantic Schema Validator        • Continuous Metric Scoring
    │                                               │
    └─────────────────────┬─────────────────────────┘
                          │
                          ▼
            [ Stage 3: Assertion Gate & Diff ]
              - Eval Score >= 0.85 Threshold?
              - Zero PII Violations?
              - Auto-generate Markdown PR Diff Report
                          │
            ┌─────────────┴─────────────┐
            ▼                           ▼
      [ PASS: Merge Allowed ]     [ FAIL: PR Blocked ]
```

---

## Key Features

* **PII & Secret Detection:** Leverages Microsoft Presidio NER and pattern scanning to detect and redact SSNs, credit cards, emails, phone numbers, and API tokens.
* **Prompt Injection & Jailbreak Defense:** Scans inputs for roleplay exploits, delimiter collisions, and system prompt exfiltration signatures.
* **Strict Schema Conformance:** Validates structured model responses against target Pydantic models.
* **LLM Evaluation Metrics:**
  * **Faithfulness / Hallucination Score:** Verifies that generated statements are grounded in retrieved context chunks.
  * **Answer Relevance Score:** Measures prompt keyword coverage to ensure topical alignment.
  * **Context Precision Score:** Evaluates whether retrieved context chunks contain relevant reference facts.
* **Automated GitHub Actions PR Bot:** Formats test results into clear Markdown comparison tables directly within PR reviews.

---

## Project Structure

```text
llm-eval-guardrails-ci/
├── .github/workflows/
│   └── eval_gate.yml            # CI workflow for linting, pytest, and eval gate
├── src/eval_pipeline/
│   ├── config/
│   │   └── settings.py          # Thresholds and pipeline configurations
│   ├── core/
│   │   └── runner.py            # Orchestrator running guardrails & evaluators
│   ├── evaluators/
│   │   ├── base.py              # Base evaluator interface
│   │   ├── context_precision.py # Context precision evaluator
│   │   ├── faithfulness.py      # Hallucination & factual consistency checker
│   │   └── relevance.py         # Prompt relevance & keyword alignment
│   ├── guardrails/
│   │   ├── injection.py         # Adversarial prompt injection scanner
│   │   ├── pii.py               # Presidio PII & secret detector
│   │   └── schema.py            # Strict Pydantic JSON validator
│   ├── models/
│   │   └── schemas.py           # Core Pydantic contracts and data models
│   ├── reporters/
│   │   ├── markdown.py          # PR Markdown comment generator
│   │   └── terminal.py          # Rich console visualizer
│   └── main.py                  # CLI entrypoint
├── tests/
│   ├── test_evaluators.py       # Async tests for LLM metric scoring
│   └── test_guardrails.py       # Unit tests for PII, injections, and schemas
├── pyproject.toml               # Project dependencies and tool configurations
└── README.md
```

---

## Quickstart

### 1. Installation

Clone the repository and install dependencies using `uv`:

```bash
git clone [https://github.com/tristanvernet/llm-eval-guardrails-ci.git](https://github.com/tristanvernet/llm-eval-guardrails-ci.git)
cd llm-eval-guardrails-ci
uv sync --all-extras --dev
uv pip install -e .
```

### 2. Run the Test Suite

Execute the unit and integration tests via `pytest`:

```bash
uv run pytest -v
```

### 3. Run the Evaluation CLI Gate

Run the evaluation engine to generate terminal analytics and export a Markdown PR report:

```bash
uv run python -m eval_pipeline.main
```

---

## Evaluation Thresholds

Default scoring thresholds can be configured via environment variables or `src/eval_pipeline/config/settings.py`:

| Parameter | Default Threshold | Description |
| :--- | :--- | :--- |
| `EVAL_MIN_FAITHFULNESS_SCORE` | `0.85` | Minimum groundedness ratio before flagging a hallucination. |
| `EVAL_MIN_RELEVANCE_SCORE` | `0.80` | Minimum prompt keyword coverage required. |
| `EVAL_MIN_CONTEXT_PRECISION_SCORE` | `0.75` | Minimum ratio of relevant retrieved chunks. |
| `EVAL_BLOCK_PROMPT_INJECTION` | `true` | Enforces zero-tolerance blocking on adversarial inputs. |

---

## License

This project is licensed under the MIT License.