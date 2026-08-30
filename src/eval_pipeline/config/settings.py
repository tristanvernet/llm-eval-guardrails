from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class PipelineSettings(BaseSettings):
    """Configuration settings for LLM evaluation and guardrails CI suite."""

    # Project directories
    project_root: Path = Path(__file__).resolve().parent.parent.parent.parent
    data_dir: Path = project_root / "data" / "golden_datasets"
    reports_dir: Path = project_root / "reports"

    # Evaluation Thresholds (0.0 to 1.0)
    min_faithfulness_score: float = 0.85
    min_relevance_score: float = 0.80
    min_context_precision_score: float = 0.75
    min_overall_score: float = 0.80

    # Guardrails Enforcement
    allow_pii_entities: list[str] = []
    block_prompt_injection: bool = True
    enforce_strict_json: bool = True

    # Execution limits
    max_latency_seconds: float = 5.0

    model_config = SettingsConfigDict(env_prefix="EVAL_", env_file=".env", extra="ignore")


settings = PipelineSettings()
