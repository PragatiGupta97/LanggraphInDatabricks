"""Schema Helper Node.

Retrieves database schema information from mock data.
"""

import mlflow
from langchain_core.messages import ToolMessage
from mlflow.entities import SpanType

from ..python_tools.get_snowflake_schema import (
    get_snowflake_schema,
)

from ..state.workflow_state import EnhancedSQLWorkflowState


@mlflow.trace(span_type=SpanType.TOOL, name="schema_helper_node")
def schema_helper_node(state: EnhancedSQLWorkflowState) -> dict:
    """Step 1: Retrieve database schema.

    Args:
        state: Current workflow state

    Returns:
        Dictionary with messages and has_error flag
    """
    print("\n" + "=" * 80)
    print("📊 Step 1: Schema Helper Agent")
    print("=" * 80)

    try:
        # Call the tool directly
        schema_info = get_snowflake_schema.invoke({"table_names": None})

        print(f"✅ Schema retrieved: {len(str(schema_info))} characters")

        # Store schema in ToolMessage for context
        return {
            "messages": [
                ToolMessage(
                    content=str(schema_info),
                    name="get_snowflake_schema",
                    tool_call_id="schema_helper_call",
                    additional_kwargs={"type": "schema"},
                )
            ],
            "has_error": False,
        }
    except Exception as e:
        error_msg = f"Failed to retrieve schema: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "messages": [
                ToolMessage(
                    content=error_msg,
                    name="get_snowflake_schema",
                    tool_call_id="schema_helper_call",
                    additional_kwargs={"is_error": True, "error": error_msg},
                )
            ],
            "has_error": True,
        }
