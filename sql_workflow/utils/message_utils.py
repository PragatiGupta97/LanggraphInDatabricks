"""Message Utilities.

Helper functions to extract information from the message-based state.
"""

from typing import Any, Optional

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage


def get_user_query(messages: list[BaseMessage]) -> str:
    """Extract the user's original query from messages.

    Args:
        messages: List of messages in the state

    Returns:
        The user's query string, or empty string if not found
    """
    for msg in messages:
        # Only get HumanMessages without a name (original user query)
        # Skip workflow-generated HumanMessages (e.g., human_approval)
        if isinstance(msg, HumanMessage) and not msg.name:
            return msg.content
    return ""


def get_latest_by_type(messages: list[BaseMessage], msg_type: type) -> Optional[BaseMessage]:
    """Get the most recent message of a specific type.

    Args:
        messages: List of messages
        msg_type: Type of message to find (HumanMessage, AIMessage, etc.)

    Returns:
        The most recent message of that type, or None if not found
    """
    for msg in reversed(messages):
        if isinstance(msg, msg_type):
            return msg
    return None


def get_schema_info(messages: list[BaseMessage]) -> str:
    """Extract schema information from messages.

    Args:
        messages: List of messages in the state

    Returns:
        Schema information as a string
    """
    for msg in reversed(messages):
        if isinstance(msg, ToolMessage) and msg.name == "get_snowflake_schema":
            return msg.content
    return ""


def get_generated_sql(messages: list[BaseMessage]) -> str:
    """Extract the generated SQL query from messages.

    Args:
        messages: List of messages in the state

    Returns:
        SQL query string
    """
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.name == "sql_generator":
            # SQL is stored in metadata or content
            if hasattr(msg, "additional_kwargs") and "sql" in msg.additional_kwargs:
                return msg.additional_kwargs["sql"]
            # Fallback: extract from content if formatted as "SQL: ..."
            content = msg.content
            if "SQL:" in content:
                return content.split("SQL:")[1].split("\n")[0].strip()
            return content
    return ""


def get_confidence_score(messages: list[BaseMessage]) -> float:
    """Extract confidence score from SQL generator message.

    Args:
        messages: List of messages in the state

    Returns:
        Confidence score (0.0-1.0), default 0.0
    """
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.name == "sql_generator":
            if hasattr(msg, "additional_kwargs") and "confidence" in msg.additional_kwargs:
                return msg.additional_kwargs["confidence"]
    return 0.0


def get_validation_result(messages: list[BaseMessage]) -> Optional[str]:
    """Extract validation result from messages.

    Args:
        messages: List of messages in the state

    Returns:
        Validation result string or None
    """
    for msg in reversed(messages):
        if isinstance(msg, ToolMessage) and msg.name == "sql_validator":
            return msg.content
    return None


def get_execution_error(messages: list[BaseMessage]) -> str:
    """Extract execution error from messages.

    Args:
        messages: List of messages in the state

    Returns:
        Error message string, or empty if no error
    """
    for msg in reversed(messages):
        if isinstance(msg, ToolMessage) and msg.name == "query_executor":
            if hasattr(msg, "additional_kwargs") and "error" in msg.additional_kwargs:
                return msg.additional_kwargs["error"]
            # Check if content indicates an error
            if msg.content.startswith("Error:") or msg.content.startswith("ERROR"):
                return msg.content
    return ""


def get_query_results(messages: list[BaseMessage]) -> Any:
    """Extract query execution results from messages.

    Args:
        messages: List of messages in the state

    Returns:
        Query results (dict or list), or None
    """
    for msg in reversed(messages):
        if isinstance(msg, ToolMessage) and msg.name == "query_executor":
            if hasattr(msg, "additional_kwargs") and "results" in msg.additional_kwargs:
                return msg.additional_kwargs["results"]
            # Try to parse content as JSON
            import json

            try:
                return json.loads(msg.content)
            except:
                return msg.content
    return None


def get_sql_explanation(messages: list[BaseMessage]) -> str:
    """Extract SQL explanation from messages.

    Args:
        messages: List of messages in the state

    Returns:
        Explanation string
    """
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.name == "sql_explainer":
            return msg.content
    return ""


def get_formatted_result(messages: list[BaseMessage]) -> str:
    """Extract formatted final result from messages.

    Args:
        messages: List of messages in the state

    Returns:
        Formatted result string
    """
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.name == "result_formatter":
            return msg.content
    return ""


def has_error_message(messages: list[BaseMessage]) -> bool:
    """Check if any message contains an error.

    Args:
        messages: List of messages in the state

    Returns:
        True if an error message is found
    """
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.name == "error_handler":
            return True
        if hasattr(msg, "additional_kwargs") and msg.additional_kwargs.get("is_error", False):
            return True
    return False
