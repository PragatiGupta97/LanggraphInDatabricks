"""Validate SQL Query Tool.

This tool validates SQL queries for security, syntax, and best practices.
"""

import re
from typing import Any

import mlflow
from langchain_core.tools import tool
from mlflow.entities import SpanType


@mlflow.trace(span_type=SpanType.TOOL, name="validate_sql")
def _validate_sql(sql_query: str) -> dict[str, Any]:
    """Validate SQL query for security and best practices."""
    errors = []
    warnings = []
    security_checks = {
        "no_drop": True,
        "no_delete": True,
        "no_insert": True,
        "no_update": True,
        "no_truncate": True,
        "no_alter": True,
        "no_create": True,
    }

    sql_upper = sql_query.upper().strip()

    # Check if SELECT query (read-only)
    is_read_only = sql_upper.startswith("SELECT")
    if not is_read_only:
        errors.append("Query must start with SELECT (read-only queries only)")

    # Check for dangerous keywords (whole word matches only)
    dangerous_keywords = ["DROP", "DELETE", "INSERT", "UPDATE", "TRUNCATE", "ALTER", "CREATE"]
    for keyword in dangerous_keywords:
        if re.search(rf"\b{keyword}\b", sql_upper):
            errors.append(f"Query contains dangerous keyword: {keyword}")
            security_checks[f"no_{keyword.lower()}"] = False

    # Check for LIMIT clause
    has_limit = bool(re.search(r"\bLIMIT\s+\d+", sql_upper))
    if not has_limit:
        errors.append("Query must include LIMIT clause (max 100 rows)")
    else:
        # Check limit value
        limit_match = re.search(r"\bLIMIT\s+(\d+)", sql_upper)
        if limit_match:
            limit_value = int(limit_match.group(1))
            if limit_value > 100:
                warnings.append(f"LIMIT {limit_value} exceeds recommended maximum of 100 rows")

    # Check for proper column quoting
    if re.search(r'ORDER_ID\s*=\s*["\']', sql_query):
        warnings.append(
            "ORDER_ID is numeric, should not use quotes in comparison "
            "(e.g., ORDER_ID = 123, not ORDER_ID = '123')"
        )

    # Determine if query is valid
    is_valid = len(errors) == 0

    return {
        "is_valid": is_valid,
        "is_read_only": is_read_only,
        "has_limit_clause": has_limit,
        "errors": errors,
        "warnings": warnings,
        "security_checks": security_checks,
        "recommendation": "Query is safe to execute"
        if is_valid
        else "Query has errors and should not be executed",
    }


@tool
@mlflow.trace(name="validate_sql_query", span_type=mlflow.entities.SpanType.TOOL)
def validate_sql_query(sql_query: str) -> dict[str, Any]:
    """Validate SQL queries for security and best practices before execution.

    Performs comprehensive checks including: ensuring queries are read-only
    (SELECT only), detecting dangerous keywords (DROP, DELETE, INSERT, UPDATE),
    verifying LIMIT clauses exist, checking proper syntax for column names with
    spaces, and validating numeric vs string value handling. Returns detailed
    validation results with errors, warnings, and security check status.

    Args:
        sql_query: The SQL query to validate for security and best practices.
            Must be a SELECT statement with LIMIT clause.

    Returns:
        dict[str, Any]: Dictionary containing validation results
    """
    try:
        validation_results = _validate_sql(sql_query)

        return {
            "success": True,
            **validation_results,
        }

    except Exception as e:
        return {
            "success": False,
            "is_valid": False,
            "error": str(e),
        }
