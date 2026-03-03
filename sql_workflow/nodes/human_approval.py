"""Human Approval Node.

Interrupts workflow to request human review of low-confidence SQL queries.
"""

import json
from typing import Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.types import interrupt
from pydantic import BaseModel, Field

from ..state.workflow_state import EnhancedSQLWorkflowState
from ..utils.llm_factory import create_llm
from ..utils.message_utils import get_confidence_score, get_generated_sql, get_user_query


class HumanApprovalResponse(BaseModel):
    """Structured response from parsing human approval text."""

    approved: bool = Field(description="Whether the SQL query is approved")
    modified_sql: Optional[str] = Field(
        default=None, description="Modified SQL query if provided by human"
    )
    reason: Optional[str] = Field(default=None, description="Reason for approval or rejection")


def parse_human_response(natural_text: str, original_sql: str) -> HumanApprovalResponse:
    """Parse natural language human response into structured format.

    Args:
        natural_text: Human's natural language response
        original_sql: The original SQL query being reviewed

    Returns:
        Parsed approval response
    """
    llm = create_llm()
    structured_llm = llm.with_structured_output(HumanApprovalResponse)

    prompt = f"""You are parsing a human's response to a SQL query approval request.

Original SQL query:
{original_sql}

Human's response:
{natural_text}

Parse the human's response and determine:
1. Did they approve or reject the SQL? (Look for words like "approve", "yes", "ok", "looks good" vs "reject", "no", "don't run")
2. Did they provide a modified SQL query? (Look for SQL code in their response)
3. What was their reasoning?

Be liberal in interpreting approval - if they seem positive or make minor corrections, consider it approved.
If they provide modified SQL, extract the complete SQL query from their response."""

    result = structured_llm.invoke(
        [
            SystemMessage(content=prompt),
            HumanMessage(content=natural_text),
        ]
    )

    return result


def human_approval_node(state: EnhancedSQLWorkflowState) -> dict:
    """Step 4: Request human approval (interrupts workflow).

    Args:
        state: Current workflow state

    Returns:
        Dictionary with human_approved, requires_human_approval, messages,
        and optionally has_error flag
    """
    print("\n" + "=" * 80)
    print("👤 Step 4: Human Approval Required")
    print("=" * 80)

    messages = state["messages"]
    user_query = get_user_query(messages)
    generated_sql = get_generated_sql(messages)
    confidence = get_confidence_score(messages)

    approval_request = {
        "message": "🔍 Human review required due to low confidence",
        "user_query": user_query,
        "generated_sql": generated_sql,
        "confidence_score": f"{confidence * 100:.1f}%",
        "reason": "Confidence below 70% threshold",
        "instructions": "Please respond in natural language to approve, reject, or modify the SQL query.",
        "examples": [
            "Looks good, run it",
            "Approved",
            "No, this is wrong",
            "Change the WHERE clause to filter by status = 'active'",
        ],
    }

    print(json.dumps(approval_request, indent=2))

    # This interrupts the workflow and waits for human input
    # The human responds in natural language (e.g., "looks good" or "change X to Y")
    human_natural_response = interrupt(approval_request)

    # Parse the natural language response using LLM
    print(f"\n📝 Human response: {human_natural_response}")
    print("🤖 Parsing response with LLM...")

    parsed_response = parse_human_response(human_natural_response, generated_sql)

    approved = parsed_response.approved
    modified_sql = parsed_response.modified_sql

    print(f"   Interpreted as: {'✅ Approved' if approved else '❌ Rejected'}")
    if modified_sql:
        print(f"   Modified SQL detected: {modified_sql[:100]}...")

    if approved:
        print("✅ Human approved the SQL")
        approval_message = "Human approved the SQL query"
        if parsed_response.reason:
            approval_message += f": {parsed_response.reason}"

        result = {
            "human_approved": True,
            "requires_human_approval": False,
            "messages": [
                HumanMessage(
                    content=approval_message,
                    name="human_approval",
                    additional_kwargs={
                        "approved": True,
                        "reason": parsed_response.reason,
                    },
                )
            ],
        }
        if modified_sql:
            # Replace the SQL in messages by adding a new SQL generator message
            result["messages"].append(
                AIMessage(
                    content=modified_sql,
                    name="sql_generator",
                    additional_kwargs={
                        "sql": modified_sql,
                        "confidence": 1.0,  # Human-modified SQL is trusted
                        "modified_by_human": True,
                    },
                )
            )
            print(f"   Modified SQL: {modified_sql[:100]}...")
        return result
    else:
        print("❌ Human rejected the SQL")
        rejection_message = "Human rejected the generated SQL"
        if parsed_response.reason:
            rejection_message += f": {parsed_response.reason}"

        return {
            "human_approved": False,
            "requires_human_approval": False,
            "has_error": True,
            "messages": [
                HumanMessage(
                    content=rejection_message,
                    name="human_approval",
                    additional_kwargs={
                        "is_error": True,
                        "error": "Human rejected SQL",
                        "reason": parsed_response.reason,
                    },
                )
            ],
        }
