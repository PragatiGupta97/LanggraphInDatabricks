"""Workflow Configuration Settings.

Contains all configuration constants and thresholds for the SQL workflow.
"""

import os
from dataclasses import dataclass


@dataclass
class WorkflowConfig:
    """Configuration for SQL workflow behavior."""

    # Confidence thresholds
    CONFIDENCE_THRESHOLD: float = 0.70  # Below this triggers human approval
    DEFAULT_CONFIDENCE: float = 0.50  # Default when confidence cannot be determined

    # Retry configuration
    MAX_RETRIES: int = 3

    # Fixable error patterns
    FIXABLE_ERROR_PATTERNS: tuple[str, ...] = (
        "does not exist",  # Table/column not found
        "syntax error",  # SQL syntax issue
        "invalid",  # Invalid query
        "ambiguous",  # Ambiguous column reference
    )

    # LLM configuration
    LLM_ENDPOINT: str = "databricks-claude-sonnet-4-5"
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 2000
    
    # Fallback to OpenAI for local testing
    USE_OPENAI_FOR_LOCAL: bool = os.getenv("USE_OPENAI_FOR_LOCAL", "false").lower() == "true"
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4")

    # Confidence level descriptions
    CONFIDENCE_GUIDELINES: str = """Confidence guidelines:
- 90-100: Very clear requirements, standard query patterns
- 70-89: Clear requirements, some assumptions
- 50-69: Ambiguous requirements, uncertain about schema
- 0-49: Very unclear requirements, major assumptions"""


# Global config instance
config = WorkflowConfig()
