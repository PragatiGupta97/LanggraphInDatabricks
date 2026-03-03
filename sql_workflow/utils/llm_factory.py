"""LLM Factory.

Factory function for creating LLM instances with consistent configuration.
"""

from typing import Union

from langchain_core.language_models import BaseChatModel

from ..config.settings import config


def create_llm() -> BaseChatModel:
    """Create and return an LLM instance.
    
    Uses ChatDatabricks by default, or falls back to OpenAI if configured
    for local testing.

    Returns:
        Configured LLM instance (ChatDatabricks or ChatOpenAI)
    """
    # Try Databricks first, fallback to OpenAI if configured
    if config.USE_OPENAI_FOR_LOCAL:
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=config.OPENAI_MODEL,
                temperature=config.LLM_TEMPERATURE,
                max_tokens=config.LLM_MAX_TOKENS,
            )
        except ImportError:
            print("⚠️  langchain-openai not installed. Install with: pip install langchain-openai")
            raise
    else:
        from databricks_langchain import ChatDatabricks
        return ChatDatabricks(
            endpoint=config.LLM_ENDPOINT,
            temperature=config.LLM_TEMPERATURE,
            max_tokens=config.LLM_MAX_TOKENS,
        )
