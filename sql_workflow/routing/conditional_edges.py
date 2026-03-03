"""Conditional Edge Functions.

Routing logic that determines workflow execution paths based on state.
"""

from ..config.settings import config
from ..state.workflow_state import EnhancedSQLWorkflowState
from ..utils.message_utils import get_schema_info


def should_continue_after_schema(state: EnhancedSQLWorkflowState) -> str:
    """Route after schema retrieval.

    Args:
        state: Current workflow state

    Returns:
        "generate" to proceed to SQL generation, "error" if schema retrieval failed
    """
    if state.get("has_error"):
        return "error"

    schema_info = get_schema_info(state["messages"])
    return "generate" if schema_info else "error"


def should_request_human_approval(state: EnhancedSQLWorkflowState) -> str:
    """Route based on confidence score.

    Args:
        state: Current workflow state

    Returns:
        "human_approval" if confidence is low, "validate" if confidence is acceptable,
        "error" if there's an error
    """
    if state.get("has_error"):
        return "error"

    if state.get("requires_human_approval", False):
        return "human_approval"
    else:
        return "validate"


def should_continue_after_approval(state: EnhancedSQLWorkflowState) -> str:
    """Route after human approval.

    Args:
        state: Current workflow state

    Returns:
        "validate" if approved, "error" if rejected
    """
    if not state.get("human_approved", False):
        return "error"
    return "validate"


def should_continue_after_validation(state: EnhancedSQLWorkflowState) -> str:
    """Route after SQL validation.
    
    Workflow ends at validation for mock example.

    Args:
        state: Current workflow state

    Returns:
        "success" if validation passed, "error" if validation failed
    """
    if state.get("has_error"):
        return "error"

    if state.get("validation_passed", False):
        return "success"
    else:
        return "error"
