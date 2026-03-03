"""SQL Generator Node.

Generates SQL queries with confidence scoring using LLM.
"""

import backoff
import mlflow
import openai
from langchain_core.messages import AIMessage, HumanMessage
from mlflow.entities import SpanType

from ..python_tools.generate_sql_query import (
    generate_sql_query,
)

from ..config.settings import config
from ..state.workflow_state import EnhancedSQLWorkflowState
from ..utils.llm_factory import create_llm
from ..utils.message_utils import (
    get_execution_error,
    get_generated_sql,
    get_schema_info,
    get_user_query,
)
from ..utils.sql_utils import clean_sql_query


@backoff.on_exception(backoff.expo, openai.RateLimitError)
@mlflow.trace(span_type=SpanType.LLM, name="sql_generator_node")
def sql_generator_with_confidence_node(state: EnhancedSQLWorkflowState) -> dict:
    """Step 2: Generate SQL with confidence score.

    Args:
        state: Current workflow state

    Returns:
        Dictionary with messages, requires_human_approval, and has_error flag
    """
    print("\n" + "=" * 80)
    print("🔧 Step 2: SQL Generator with Confidence Scoring")
    print("=" * 80)

    if state.get("has_error"):
        return {}

    llm = create_llm()
    messages = state["messages"]

    try:
        # Extract information from messages
        user_query = get_user_query(messages)
        schema_info = get_schema_info(messages)

        # Include retry context if this is a retry
        retry_context = ""
        if state.get("retry_count", 0) > 0:
            previous_error = get_execution_error(messages)
            previous_sql = get_generated_sql(messages)
            retry_context = (
                f"\n\nPREVIOUS ATTEMPT FAILED:\n"
                f"Error: {previous_error}\n"
                f"Previous SQL: {previous_sql}\n\n"
                f"Please fix the issue and generate corrected SQL."
            )

        # Use LLM to generate SQL with confidence
        prompt = f"""You are a SQL Generator Agent. Generate a SQL query and rate your confidence.

User's Question: {user_query}

Schema information:
{schema_info}{retry_context}

Provide your response in this EXACT format:

SQL: <your_sql_query>
CONFIDENCE: <0-100>
REASONING: <why this confidence level>

IMPORTANT: Return ONLY the SQL query without any markdown code fences (```sql), comments, or explanations in the SQL section.

{config.CONFIDENCE_GUIDELINES}"""

        response = llm.invoke([HumanMessage(content=prompt)])
        output = response.content

        # Parse SQL and confidence from output
        sql_query = ""
        confidence = config.DEFAULT_CONFIDENCE

        # Extract SQL
        if "SQL:" in output:
            sql_part = output.split("SQL:")[1].split("CONFIDENCE:")[0].strip()
            sql_query = clean_sql_query(sql_part)
        else:
            # Call the tool to generate SQL
            sql_result = generate_sql_query.invoke(
                {
                    "natural_language_query": user_query,
                    "schema_info": schema_info,
                }
            )
            sql_query = clean_sql_query(str(sql_result))

        # Extract confidence
        if "CONFIDENCE:" in output:
            try:
                conf_str = output.split("CONFIDENCE:")[1].split("\n")[0].strip()
                confidence = float(conf_str) / 100.0  # Convert to 0-1 scale
            except:
                confidence = config.DEFAULT_CONFIDENCE

        print("✅ SQL Generated:")
        print(f"   Query: {str(sql_query)[:100]}...")
        print(f"   Confidence: {confidence * 100:.1f}%")

        # Determine if human approval needed
        requires_approval = confidence < config.CONFIDENCE_THRESHOLD

        if requires_approval:
            print("⚠️  Low confidence - Human approval will be required")

        # Store SQL and metadata in AIMessage
        return {
            "messages": [
                AIMessage(
                    content=str(sql_query),
                    name="sql_generator",
                    additional_kwargs={
                        "sql": str(sql_query),
                        "confidence": confidence,
                        "reasoning": output if "REASONING:" in output else "Generated SQL query",
                    },
                )
            ],
            "requires_human_approval": requires_approval,
            "has_error": False,
        }
    except Exception as e:
        error_msg = f"Failed to generate SQL: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "messages": [
                AIMessage(
                    content=error_msg,
                    name="sql_generator",
                    additional_kwargs={"is_error": True, "error": error_msg},
                )
            ],
            "has_error": True,
        }
