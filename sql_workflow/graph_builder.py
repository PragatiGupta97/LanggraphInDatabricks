"""Workflow Graph Builder.

Constructs the LangGraph workflow with all nodes and routing logic.
"""

from langgraph.graph import END, START, StateGraph

from .nodes import (
    error_handler_node,
    human_approval_node,
    schema_helper_node,
    sql_generator_with_confidence_node,
    sql_validator_node,
)
from .nodes.confidence_router import confidence_router_node
from .routing import (
    should_continue_after_approval,
    should_continue_after_schema,
    should_continue_after_validation,
    should_request_human_approval,
)
from .state import EnhancedSQLWorkflowState


def create_enhanced_sql_workflow() -> StateGraph:
    """Create the enhanced SQL workflow graph with all nodes and edges.
    
    Workflow stops at SQL validation - this is a mock example for testing.

    Returns:
        Compiled StateGraph ready for execution
    """
    print("\n" + "=" * 80)
    print("🏗️  Building SQL Workflow Graph (Mock Example)")
    print("=" * 80)

    # Initialize the graph
    workflow = StateGraph(EnhancedSQLWorkflowState)

    # Add nodes (stopping at validation for mock example)
    workflow.add_node("schema_helper", schema_helper_node)
    workflow.add_node("sql_generator", sql_generator_with_confidence_node)
    workflow.add_node("confidence_router", confidence_router_node)
    workflow.add_node("human_approval", human_approval_node)
    workflow.add_node("sql_validator", sql_validator_node)
    workflow.add_node("error_handler", error_handler_node)

    # Define the workflow edges
    workflow.add_edge(START, "schema_helper")

    # After schema: generate SQL or handle error
    workflow.add_conditional_edges(
        "schema_helper",
        should_continue_after_schema,
        {
            "generate": "sql_generator",
            "error": "error_handler",
        },
    )

    # After SQL generation: check confidence
    workflow.add_edge("sql_generator", "confidence_router")

    # After confidence router: human approval or validation
    workflow.add_conditional_edges(
        "confidence_router",
        should_request_human_approval,
        {
            "human_approval": "human_approval",
            "validate": "sql_validator",
            "error": "error_handler",
        },
    )

    # After human approval: proceed to validation
    workflow.add_conditional_edges(
        "human_approval",
        should_continue_after_approval,
        {
            "validate": "sql_validator",
            "error": "error_handler",
        },
    )

    # After validation: end the workflow (mock example stops here)
    workflow.add_conditional_edges(
        "sql_validator",
        should_continue_after_validation,
        {
            "success": END,
            "error": "error_handler",
        },
    )

    # Error handler ends the workflow
    workflow.add_edge("error_handler", END)

    print("✅ Workflow graph constructed successfully (stops at validation)")

    return workflow
