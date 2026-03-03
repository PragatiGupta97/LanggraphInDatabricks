"""SQL Multi-Agent Workflow Package.

This package contains the enhanced SQL workflow with human-in-the-loop capabilities,
confidence-based routing, retry logic, and comprehensive error handling.
"""

# Lazy imports to avoid loading heavy dependencies on package import
__all__ = ["create_enhanced_sql_workflow"]


def __getattr__(name):
    """Lazy loading of workflow components."""
    if name == "create_enhanced_sql_workflow":
        from .graph_builder import create_enhanced_sql_workflow

        return create_enhanced_sql_workflow
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
