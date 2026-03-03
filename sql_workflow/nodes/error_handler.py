"""Error Handler Node.

Handles errors and provides user-friendly error messages.
"""

from langchain_core.messages import AIMessage

from ..state.workflow_state import EnhancedSQLWorkflowState


def error_handler_node(state: EnhancedSQLWorkflowState) -> dict:
    """Handle errors and provide user-friendly messages.

    Args:
        state: Current workflow state

    Returns:
        Dictionary with messages containing error information
    """
    print("\n" + "=" * 80)
    print("❌ Error Handler")
    print("=" * 80)

    # Extract error from messages
    messages = state["messages"]
    error_msg = "Unknown error occurred"

    # Find the most recent error message
    for msg in reversed(messages):
        if hasattr(msg, "additional_kwargs"):
            if msg.additional_kwargs.get("is_error"):
                error_msg = msg.additional_kwargs.get("error", msg.content)
                break
            elif msg.additional_kwargs.get("error"):
                error_msg = msg.additional_kwargs["error"]
                break

    print(f"Error: {error_msg}")

    return {
        "messages": [
            AIMessage(
                content=f"I encountered an error: {error_msg}. Please check your query and try again.",
                name="error_handler",
                additional_kwargs={"is_error": True, "error": error_msg, "type": "final_error"},
            )
        ]
    }
