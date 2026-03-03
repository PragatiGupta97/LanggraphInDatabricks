"""Workflow State Definition.

Defines the state schema for the enhanced SQL workflow using message-based architecture.
"""

import operator
from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import BaseMessage


class EnhancedSQLWorkflowState(TypedDict):
    """Message-centric state schema for SQL workflow.

    This refactored state uses messages as the primary data container, following
    LangGraph best practices. Information flows through the workflow via messages
    with metadata, rather than separate state fields.

    Message Types Used:
        - HumanMessage: User queries
        - SystemMessage: Schema information, context
        - AIMessage: Generated SQL, explanations, formatted results
        - ToolMessage: Validation results, query execution results

    Attributes:
        messages: Primary state container - all conversation and data flow
        retry_count: Number of retry attempts (control flow)
        requires_human_approval: Flag for human-in-the-loop (control flow)
        human_approved: User's approval decision (control flow)
        validation_passed: Boolean flag for validation (control flow)
        has_error: Quick error flag for routing (control flow)
    """

    messages: Annotated[Sequence[BaseMessage], operator.add]
    retry_count: int
    requires_human_approval: bool
    human_approved: bool
    validation_passed: bool
    has_error: bool
