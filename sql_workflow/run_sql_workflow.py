"""Run Enhanced SQL Multi-Agent Workflow - Local Testing Entry Point.

This script is for local testing of the SQL workflow orchestrator.
For MLflow deployment, use create_sql_workflow.py as a template.

STREAMING PATTERN:
------------------
The SQLWorkflowOrchestrator follows the same streaming pattern as the main agent
in src/mose_ai_assistant/agent/agent.py:

1. Uses Generator[ResponsesAgentStreamEvent, None, None] for streaming
2. Yields events progressively as workflow steps complete
3. Uses yield from output_to_responses_items_stream() for message conversion
4. Streams intermediate results (SQL generation, validation, execution)
5. Provides real-time progress updates to users

TESTING STREAMING:
------------------
This script tests both streaming modes:
1. LangGraph native streaming (app.stream()) - for development/debugging
2. ResponsesAgent streaming (predict_stream()) - for production deployment

Example usage:
    # Development: Direct LangGraph streaming
    for event in app.stream(initial_state, config):
        print(event)

    # Production: ResponsesAgent streaming (matches MLflow deployment)
    from mlflow.types.responses import ResponsesAgentRequest
    request = ResponsesAgentRequest(input=[...])
    for event in orchestrator.predict_stream(request):
        print(event)
"""

import json
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

# Load environment variables from .env file BEFORE other imports
# File is at: sql_workflow/run_sql_workflow.py
# Need to go up 2 levels to reach project root
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded environment variables from {env_path}")
else:
    print(f"⚠️  Warning: .env file not found at {env_path}")

# Import from local package (relative to workspace)
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from sql_workflow.sql_workflow_databricks import SQLWorkflowOrchestrator


def test_responses_agent_streaming(orchestrator: SQLWorkflowOrchestrator, query: str):
    """Test the ResponsesAgent streaming interface (production mode).

    This demonstrates how the workflow streams when deployed via MLflow,
    matching the streaming pattern in agent.py.

    Args:
        orchestrator: The SQLWorkflowOrchestrator instance
        query: User query to process
    """
    from mlflow.types.responses import (
        ResponsesAgentRequest,
        ResponsesAgentRequestInput,
    )

    print("\n" + "=" * 80)
    print("🧪 Testing ResponsesAgent Streaming (Production Mode)")
    print("=" * 80)
    print(f"\n🔍 Query: {query}")
    print("\n📡 Streaming ResponsesAgentStreamEvents:\n" + "─" * 80)

    # Create a ResponsesAgentRequest (same as what MLflow would send)
    request = ResponsesAgentRequest(input=[ResponsesAgentRequestInput(role="user", content=query)])

    # Stream events like agent.py does
    event_count = 0
    for event in orchestrator.predict_stream(request):
        event_count += 1
        event_type = event.type

        # Display stream events
        if event_type == "response.output_item.done":
            item = event.item
            if hasattr(item, "text_content"):
                print(f"\n[Event {event_count}] {event_type}")
                print(f"  Content: {item.text_content[:150]}...")
            elif hasattr(item, "content"):
                print(f"\n[Event {event_count}] {event_type}")
                print(f"  Content: {str(item.content)[:150]}...")
        else:
            print(f"\n[Event {event_count}] {event_type}")

    print("\n" + "─" * 80)
    print(f"✅ Streaming complete - {event_count} events yielded")


def display_results(state: dict):
    """Display formatted workflow results (stops at validation).

    Args:
        state: Final workflow state dictionary
    """
    from sql_workflow.utils.message_utils import (
        get_confidence_score,
        get_generated_sql,
        get_validation_result,
    )

    print("\n" + "=" * 80)
    print("WORKFLOW RESULTS (Mock Example - Stops at Validation)")
    print("=" * 80)

    messages = state.get("messages", [])

    # Generated SQL
    generated_sql = get_generated_sql(messages)
    if generated_sql:
        print("\n✅ Generated SQL:")
        print("─" * 80)
        print(generated_sql)
        print("─" * 80)
        confidence = get_confidence_score(messages)
        print(f"Confidence Score: {confidence * 100:.1f}%")

    # Validation Status
    validation_result = get_validation_result(messages)
    if validation_result:
        is_valid = "invalid" not in validation_result.lower()
        status = "✅ PASSED" if is_valid else "❌ FAILED"
        print(f"\n{status} SQL Validation")
        if not is_valid:
            print(f"   Details: {validation_result}")

    # Human Approval Status
    if state.get("requires_human_approval"):
        approval_status = "✅ APPROVED" if state.get("human_approved") else "⏸️  PENDING"
        print(f"\n{approval_status} Human Approval")

    # Error Information
    if state.get("has_error"):
        for msg in reversed(messages):
            if hasattr(msg, "additional_kwargs") and msg.additional_kwargs.get("is_error"):
                error_msg = msg.additional_kwargs.get("error", msg.content)
                print(f"\n❌ Error: {error_msg}")
                break

    # Retry Information
    retry_count = state.get("retry_count", 0)
    if retry_count > 0:
        print(f"\n🔄 Retry Attempts: {retry_count}")
    
    print("\n" + "=" * 80)
    print("Note: Workflow stops at validation (no execution for mock example)")
    print("=" * 80)


def main():
    """Run the SQL workflow mock example (stops at validation)."""
    print("\n" + "=" * 80)
    print("🚀 SQL Workflow - Mock Example (Databricks Compatible)")
    print("=" * 80)
    print("\n📦 Using modular structure from: sql_workflow/")
    print("✨ Workflow stops at SQL validation (no actual execution)")
    print("🎭 Uses mock data for schema and results")

    # Use Databricks-compatible orchestrator
    print("\n🔧 Building Databricks-compatible orchestrator...")
    orchestrator = SQLWorkflowOrchestrator(model="databricks-meta-llama-3-1-70b-instruct")
    app = orchestrator.agent

    # Save the workflow graph visualization
    print("\n💾 Saving workflow graph...")
    try:
        graph_png = app.get_graph().draw_mermaid_png()
        graph_path = Path(__file__).parent / "sql_workflow_graph.png"
        with open(graph_path, "wb") as f:
            f.write(graph_png)
        print(f"   ✅ Graph saved to: {graph_path}")
    except Exception as e:
        print(f"   ⚠️  Graph saving failed: {e}")

    test_query = "Which customer placed maximum orders in the last month?"

    # Initialize workflow state using message-based architecture
    initial_state = {
        "messages": [HumanMessage(content=test_query)],
        "retry_count": 0,
        "requires_human_approval": False,
        "human_approved": False,
        "validation_passed": False,
        "has_error": False,
    }

    # Configuration for this execution
    run_config = {"configurable": {"thread_id": "notebook_session_1"}}

    print(f"\n🔍 Query: {test_query}")
    print("\n⚙️  Starting workflow execution...\n")

    try:
        # Stream the workflow execution with real-time progress updates
        print("📡 Streaming workflow events:\n" + "─" * 80)

        for event in app.stream(initial_state, run_config):
            node_name = list(event.keys())[0]
            node_output = event[node_name]

            # Display node completion with visual feedback
            print(f"\n✓ Node: {node_name}")

            # Show intermediate results if available
            if node_output and isinstance(node_output, dict):
                messages = node_output.get("messages", [])
                if messages:
                    # Display last message content if it's informative
                    last_msg = messages[-1]
                    if hasattr(last_msg, "content") and last_msg.content:
                        content_preview = str(last_msg.content)[:200]
                        if len(str(last_msg.content)) > 200:
                            content_preview += "..."
                        print(f"  └─ {content_preview}")

        print("\n" + "─" * 80)

        # Get the complete final state after streaming completes
        final_state = app.get_state(run_config).values

        # Display results
        print("\n" + "=" * 80)
        print("✅ Workflow Execution Complete")
        print("=" * 80)

        if final_state:
            display_results(final_state)
        else:
            print("\n⚠️  No final state captured")

        # Optional: Test ResponsesAgent streaming interface (production mode)
        print("\n" + "=" * 80)
        print("🔄 Would you like to test ResponsesAgent streaming? (y/n)")
        print("   This shows how streaming works in production/MLflow deployment")
        print("=" * 80)

        # Auto-run for demo purposes - in interactive mode, you could ask for input
        import os

        if os.getenv("TEST_RESPONSES_STREAMING", "").lower() == "true":
            test_responses_agent_streaming(orchestrator, test_query)

    except Exception as e:
        print(f"\n❌ Workflow error: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
