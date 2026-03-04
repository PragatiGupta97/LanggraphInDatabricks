"""SQL Validator Node.

Validates SQL queries for security and correctness.
"""

import mlflow
from langchain_core.messages import ToolMessage
from mlflow.entities import SpanType

from ..python_tools.validate_sql_query import (
    validate_sql_query,
)

from ..state.workflow_state import EnhancedSQLWorkflowState
from ..utils.message_utils import get_generated_sql


@mlflow.trace(span_type=SpanType.AGENT, name="sql_validator_node")
def sql_validator_node(state: EnhancedSQLWorkflowState) -> dict:
    """Step 5: Validate SQL for security and correctness.

    Args:
        state: Current workflow state

    Returns:
        Dictionary with messages, validation_passed flag, and has_error
    """
    print("\n" + "=" * 80)
    print("🔍 Step 5: SQL Validator")
    print("=" * 80)

    if state.get("has_error"):
        return {}

    try:
        # Extract SQL from messages
        sql_query = get_generated_sql(state["messages"])

        # Call validation tool directly
        validation_output = validate_sql_query.invoke({"sql_query": sql_query})

        is_valid = (
            "valid" in str(validation_output).lower()
            and "invalid" not in str(validation_output).lower()
        )

        if is_valid:
            print("✅ SQL validation passed")
        else:
            print(f"⚠️ SQL validation issues: {validation_output}")

        return {
            "messages": [
                ToolMessage(
                    content=str(validation_output),
                    name="sql_validator",
                    tool_call_id="validation_1",
                    additional_kwargs={"is_valid": is_valid, "is_error": not is_valid},
                )
            ],
            "validation_passed": is_valid,
            "has_error": not is_valid,
        }
    except Exception as e:
        error_msg = f"Failed to validate SQL: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "messages": [
                ToolMessage(
                    content=error_msg,
                    name="sql_validator",
                    tool_call_id="validation_1",
                    additional_kwargs={"is_error": True, "error": error_msg},
                )
            ],
            "validation_passed": False,
            "has_error": True,
        }
