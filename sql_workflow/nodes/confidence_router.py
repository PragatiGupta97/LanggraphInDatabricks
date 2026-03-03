"""Confidence Router Node.

Routes workflow based on confidence score (informational node).
"""

from ..state.workflow_state import EnhancedSQLWorkflowState
from ..utils.message_utils import get_confidence_score


def confidence_router_node(state: EnhancedSQLWorkflowState) -> dict:
    """Step 3: Route based on confidence score.

    This is primarily an informational node that logs the routing decision.
    Actual routing is done by conditional edges.

    Args:
        state: Current workflow state

    Returns:
        Empty dictionary (no state updates)
    """
    print("\n" + "=" * 80)
    print("🚦 Step 3: Confidence Router")
    print("=" * 80)

    confidence = get_confidence_score(state["messages"])
    requires_approval = state.get("requires_human_approval", False)

    if requires_approval:
        print(f"🔴 Confidence {confidence * 100:.1f}% < 70% → Routing to Human Approval")
    else:
        print(f"🟢 Confidence {confidence * 100:.1f}% ≥ 70% → Proceeding to Validation")

    return {}
