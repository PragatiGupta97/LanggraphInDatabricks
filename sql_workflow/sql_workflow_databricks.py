"""Enhanced SQL Multi-Agent Workflow - Databricks Compatible Orchestrator.

This module contains the SQLWorkflowOrchestrator class that wraps the refactored
SQL workflow for Databricks Model Serving compatibility.

DATABRICKS COMPATIBILITY:
-------------------------
The SQLWorkflowOrchestrator class implements the ResponsesAgent interface, making
it compatible with MLflow and Databricks Model Serving. This follows the same pattern
as the BaseOrchestrator in src/mose_ai_assistant/agent/orchestrator.py.

KEY FEATURES:
- ResponsesAgent implementation for MLflow deployment
- Streaming and synchronous prediction methods
- Compatible with Databricks Model Serving endpoints
- Uses LangGraph with checkpoint support for human approval interrupts
- Integrates with Databricks WorkspaceClient for authentication

USAGE:
------
For local testing:
    python -m mose_ai_assistant.agent.sql_workflow.run_sql_workflow
    # or:
    python src/mose_ai_assistant/agent/sql_workflow/run_sql_workflow.py

For MLflow deployment:
    import mlflow
    from mose_ai_assistant.agent.sql_workflow_databricks import SQLWorkflowOrchestrator

    orchestrator = SQLWorkflowOrchestrator(model="databricks-meta-llama-3-1-70b-instruct")
    mlflow.pyfunc.log_model(
        artifact_path="sql_workflow_orchestrator",
        python_model=orchestrator,
        ...
    )
"""

import json
from typing import Generator
from uuid import uuid4

from databricks.sdk import WorkspaceClient
from langgraph.checkpoint.memory import MemorySaver
from mlflow.pyfunc import ResponsesAgent
from mlflow.types.responses import (
    ResponsesAgentRequest,
    ResponsesAgentResponse,
    ResponsesAgentStreamEvent,
    output_to_responses_items_stream,
    to_chat_completions_input,
)

# Import the refactored workflow
from sql_workflow import create_enhanced_sql_workflow


class SQLWorkflowOrchestrator(ResponsesAgent):  # type: ignore[subclass]
    """Databricks-compatible SQL workflow orchestrator.

    This class wraps the LangGraph SQL workflow to work with MLflow's
    ResponsesAgent interface, enabling deployment via Databricks Model Serving.
    """

    def __init__(
        self,
        model: str = "databricks-meta-llama-3-1-70b-instruct",
    ):
        """Initialize the SQL Workflow Orchestrator.

        Args:
            model: The foundation model endpoint name to use
        """
        self.model = model
        # WorkspaceClient is only needed when deployed to Databricks
        # For local testing, we can skip this initialization
        try:
            self.workspace_client = WorkspaceClient()
        except ValueError:
            # No Databricks credentials configured - OK for local testing
            self.workspace_client = None

        # Create the SQL workflow
        workflow = create_enhanced_sql_workflow()

        # Compile with checkpointing for human approval interrupts
        memory = MemorySaver()
        self.agent = workflow.compile(checkpointer=memory, interrupt_before=["human_approval"])

    def predict(self, request: ResponsesAgentRequest) -> ResponsesAgentResponse:
        """Synchronous prediction method."""
        outputs = [
            event.item
            for event in self.predict_stream(request)
            if event.type == "response.output_item.done"
        ]
        return ResponsesAgentResponse(output=outputs, custom_outputs=request.custom_inputs)

    def predict_stream(
        self,
        request: ResponsesAgentRequest,
    ) -> Generator[ResponsesAgentStreamEvent, None, None]:
        """Streaming prediction method with progressive result updates."""
        cc_msgs = to_chat_completions_input([i.model_dump() for i in request.input])
        first_message = True
        seen_ids = set()

        # Extract user query from the last message
        user_query = ""
        if cc_msgs:
            last_msg = cc_msgs[-1]
            if hasattr(last_msg, "content"):
                user_query = last_msg.content
            elif isinstance(last_msg, dict):
                user_query = last_msg.get("content", "")

        # Generate a unique thread_id for this request
        # In production, you might want to use conversation_id from request.context if available
        thread_id = str(uuid4())
        if request.context:
            conversation_id = getattr(request.context, "conversation_id", None)
            if conversation_id:
                thread_id = conversation_id

        # Configuration for LangGraph with checkpointing
        config = {"configurable": {"thread_id": thread_id}}

        # Initialize complete workflow state using message-based architecture
        from langchain_core.messages import HumanMessage

        initial_state = {
            "messages": [HumanMessage(content=user_query)],
            "retry_count": 0,
            "requires_human_approval": False,
            "human_approved": False,
            "validation_passed": False,
            "has_error": False,
        }

        # Track the final state to return results
        final_state = initial_state.copy()

        # Stream events from LangGraph agent
        for _, events in self.agent.stream(initial_state, config, stream_mode=["updates"]):
            # Accumulate state updates and stream node-specific results
            for node_name, node_output in events.items():
                if node_output is not None and isinstance(node_output, dict):
                    final_state.update(node_output)
                    yield from self._stream_node_results(node_name, node_output)

            # Extract new messages from node outputs
            new_msgs = [
                msg
                for v in events.values()
                if v is not None
                for msg in v.get("messages", [])
                if msg.id not in seen_ids
            ]

            # On first iteration, skip the input messages we sent
            if first_message:
                input_msg_count = len(cc_msgs)
                seen_ids.update(msg.id for msg in new_msgs[:input_msg_count])
                new_msgs = new_msgs[input_msg_count:]
                first_message = False

            # Track and stream new messages
            if new_msgs:
                seen_ids.update(msg.id for msg in new_msgs)
                yield from output_to_responses_items_stream(new_msgs)

        # After workflow completes, yield final summary
        if final_state:
            if final_state.get("has_error"):
                # Stream error information
                yield from self._stream_error_results(final_state)
            else:
                # Stream final formatted summary
                result_text = self._format_final_results(final_state)
                yield ResponsesAgentStreamEvent(
                    type="response.output_item.done",
                    item=self.create_text_output_item(text=result_text, id=str(uuid4())),
                )

    def _stream_node_results(
        self, node_name: str, node_output: dict
    ) -> Generator[ResponsesAgentStreamEvent, None, None]:
        """Stream intermediate results as each node completes.

        Similar to how agent.py yields tool results immediately,
        this streams workflow step results as they become available.

        Args:
            node_name: Name of the completed node
            node_output: Output dictionary from the node

        Yields:
            ResponsesAgentStreamEvent with intermediate results
        """
        from .utils.message_utils import (
            get_confidence_score,
            get_generated_sql,
            get_query_results,
            get_validation_result,
        )

        messages = node_output.get("messages", [])

        # Stream SQL generation results immediately
        if node_name == "generate_sql":
            generated_sql = get_generated_sql(messages)
            if generated_sql:
                confidence = get_confidence_score(messages)
                result_text = f"**SQL Generated** (Confidence: {confidence * 100:.1f}%)\n```sql\n{generated_sql}\n```"
                yield ResponsesAgentStreamEvent(
                    type="response.output_item.done",
                    item=self.create_text_output_item(text=result_text, id=str(uuid4())),
                )

        # Stream validation results immediately
        elif node_name == "validate_sql":
            validation_result = get_validation_result(messages)
            if validation_result:
                is_valid = "invalid" not in validation_result.lower()
                status = "Validation Passed" if is_valid else "Validation Issues"
                result_text = f"**{status}**\n{validation_result}"
                yield ResponsesAgentStreamEvent(
                    type="response.output_item.done",
                    item=self.create_text_output_item(text=result_text, id=str(uuid4())),
                )

        # Stream query execution progress
        elif node_name == "execute_query":
            query_results = get_query_results(messages)
            if query_results:
                row_count = len(query_results) if isinstance(query_results, list) else 1
                result_text = f"**Query Executed Successfully**\nRetrieved {row_count} row(s)"
                yield ResponsesAgentStreamEvent(
                    type="response.output_item.done",
                    item=self.create_text_output_item(text=result_text, id=str(uuid4())),
                )

    def _stream_error_results(
        self, state: dict
    ) -> Generator[ResponsesAgentStreamEvent, None, None]:
        """Stream error information when workflow fails.

        Args:
            state: Final workflow state with error

        Yields:
            ResponsesAgentStreamEvent with error details
        """
        messages = state.get("messages", [])
        for msg in reversed(messages):
            if hasattr(msg, "additional_kwargs") and msg.additional_kwargs.get("is_error"):
                error_msg = msg.additional_kwargs.get("error", msg.content)
                retry_count = state.get("retry_count", 0)

                error_text = f"**Workflow Error**\n\n{error_msg}"
                if retry_count > 0:
                    error_text += f"\n\nRetry attempts: {retry_count}"

                yield ResponsesAgentStreamEvent(
                    type="response.output_item.done",
                    item=self.create_text_output_item(text=error_text, id=str(uuid4())),
                )
                break

    def _format_final_results(self, state: dict) -> str:
        """Format the final workflow state into a readable response.

        Args:
            state: Final workflow state

        Returns:
            Formatted string with SQL query, explanation, and results
        """
        from .utils.message_utils import (
            get_confidence_score,
            get_formatted_result,
            get_generated_sql,
            get_query_results,
            get_sql_explanation,
        )

        result_parts = []

        # Check for errors in messages
        if state.get("has_error"):
            messages = state.get("messages", [])
            for msg in reversed(messages):
                if hasattr(msg, "additional_kwargs") and msg.additional_kwargs.get("is_error"):
                    error_msg = msg.additional_kwargs.get("error", msg.content)
                    result_parts.append(f"Error: {error_msg}")
                    return "\n".join(result_parts)

        messages = state.get("messages", [])

        # If we have a formatted result from the LLM, use that primarily
        formatted_result = get_formatted_result(messages)
        if formatted_result:
            result_parts.append("Result:")
            result_parts.append(formatted_result)
            result_parts.append("")  # Add blank line

        # Add generated SQL
        generated_sql = get_generated_sql(messages)
        if generated_sql:
            result_parts.append("Generated SQL Query:")
            result_parts.append("```sql")
            result_parts.append(generated_sql)
            result_parts.append("```")

            # Add confidence score
            confidence = get_confidence_score(messages)
            result_parts.append(f"\nConfidence Score: {confidence * 100:.1f}%")

        # Add SQL explanation
        sql_explanation = get_sql_explanation(messages)
        if sql_explanation:
            result_parts.append(f"\nExplanation:\n{sql_explanation}")

        # Add raw query results only if formatted result is not available
        if not formatted_result:
            query_results = get_query_results(messages)
            if query_results:
                result_parts.append("\nQuery Results:")
                result_parts.append("```json")
                result_parts.append(json.dumps(query_results, indent=2))
                result_parts.append("```")

        return "\n".join(result_parts)
