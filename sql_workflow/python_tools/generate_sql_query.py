"""Generate SQL Query Tool.

This tool converts natural language questions into Snowflake SQL queries using LLM.
"""

import os
from typing import Any

import backoff
import mlflow
import openai
from langchain_core.tools import tool
from mlflow.entities import SpanType


@mlflow.trace(span_type=SpanType.TOOL, name="generate_sql_with_llm")
@backoff.on_exception(backoff.expo, openai.RateLimitError)
def _generate_sql(natural_language_query: str, schema_info: str) -> str:
    """Generate SQL from natural language using LLM."""
    prompt = f"""You are a SQL expert. Generate a safe, read-only SQL query based on this question:

USER QUESTION: {natural_language_query}

SCHEMA INFORMATION:
{schema_info}

CRITICAL RULES:
1. Generate ONLY the SQL query - no explanation, no markdown, no code blocks
2. Use proper SQL syntax
3. ALWAYS include LIMIT 100 or less
4. Use double quotes for column names with spaces
5. Do NOT use quotes for numeric values in WHERE clauses (e.g., ORDER_ID = 123, not ORDER_ID = '123')
6. Only generate SELECT queries (read-only)
7. Order results logically when appropriate

IMPORTANT - ORDER IDENTIFIER DISTINCTION:
- ORDER_ID: Numeric column (NUMBER) - use when user provides ONLY digits
  * Query: WHERE ORDER_ID = 4235779 (no quotes)
- "Order No": VARCHAR column - use when user provides letters + numbers
  * Query: WHERE "Order No" = 'ABM000359' (with quotes)

Return only the raw SQL query."""

    # Try Databricks first, fallback to OpenAI
    use_openai = os.getenv("USE_OPENAI_FOR_LOCAL", "false").lower() == "true"
    
    if use_openai:
        # Use OpenAI client directly
        from openai import OpenAI
        client = OpenAI()
        model = os.getenv("OPENAI_MODEL", "gpt-4")
    else:
        # Use Databricks serving endpoint
        from databricks.sdk import WorkspaceClient
        ws = WorkspaceClient()
        client = ws.serving_endpoints.get_open_ai_client()
        model = "databricks-meta-llama-3-1-70b-instruct"

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    sql = response.choices[0].message.content.strip()

    # Clean up any markdown formatting
    sql = sql.replace("```sql", "").replace("```", "").strip()

    return sql


@tool
def generate_sql_query(natural_language_query: str, schema_info: str) -> dict[str, Any]:
    """Convert natural language questions into valid SQL queries.

    Uses schema information and LLM to generate syntactically correct SQL.
    Handles complex queries including filtering, joins, aggregations, and
    proper handling of column names with spaces. Distinguishes between
    numeric ORDER_ID and alphanumeric Order No columns.

    Args:
        natural_language_query: Natural language question to convert to SQL.
            Examples: 'Show me order 12345', 'Get all orders from last week',
            'Count orders for customer ABC123'
        schema_info: JSON string containing database schema information from
            get_snowflake_schema tool. This provides table structure, column names,
            and data types needed for SQL generation.

    Returns:
        dict[str, Any]: Dictionary containing generated SQL and metadata
    """
    try:
        sql = _generate_sql(natural_language_query, schema_info)

        return {
            "success": True,
            "sql_query": sql,
            "explanation": f"Generated SQL query for: {natural_language_query}",
            "confidence": 0.95,
        }

    except Exception as e:
        return {
            "success": False,
            "sql_query": None,
            "explanation": None,
            "error": str(e),
        }
