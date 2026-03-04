"""Get Mock Database Schema Tool.

This tool retrieves mock database schema information for sample tables.
"""

from typing import Any

import mlflow
from langchain_core.tools import tool
from mlflow.entities import SpanType


@mlflow.trace(span_type=SpanType.TOOL, name="get_schema_info")
def _get_schema_info(table_names: list[str] | None = None) -> dict[str, Any]:
    """Get schema information for specified tables or all tables (MOCK DATA)."""
    schema_info = {
        "tables": [
            {
                "table_name": "ORDERS",
                "description": "Contains order information including customer details, order status, and pricing.",
                "columns": [
                    {
                        "name": "ORDER_ID",
                        "type": "NUMBER(38,0)",
                        "description": "Unique order identifier (numeric). Primary key.",
                        "nullable": False,
                        "is_numeric": True,
                    },
                    {
                        "name": "ORDER_NUMBER",
                        "type": "VARCHAR(100)",
                        "description": "Human-readable order number.",
                        "nullable": True,
                        "is_numeric": False,
                    },
                    {
                        "name": "ORDER_DATE",
                        "type": "DATE",
                        "description": "Date when the order was created. Format: YYYY-MM-DD.",
                        "nullable": True,
                        "is_numeric": False,
                    },
                    {
                        "name": "ORDER_STATUS",
                        "type": "VARCHAR(50)",
                        "description": "Current status of the order (e.g., 'Pending', 'Shipped', 'Delivered', 'Cancelled').",
                        "nullable": True,
                        "is_numeric": False,
                    },
                    {
                        "name": "CUSTOMER_ID",
                        "type": "NUMBER(38,0)",
                        "description": "Customer identifier. Foreign key to CUSTOMERS table.",
                        "nullable": True,
                        "is_numeric": True,
                    },
                    {
                        "name": "CUSTOMER_NAME",
                        "type": "VARCHAR(100)",
                        "description": "Customer name.",
                        "nullable": True,
                        "is_numeric": False,
                    },
                    {
                        "name": "TOTAL_AMOUNT",
                        "type": "NUMBER(15,2)",
                        "description": "Total order amount in USD.",
                        "nullable": True,
                        "is_numeric": True,
                    },
                    {
                        "name": "CURRENCY",
                        "type": "VARCHAR(3)",
                        "description": "Currency code (e.g., 'USD', 'EUR', 'GBP').",
                        "nullable": True,
                        "is_numeric": False,
                    },
                    {
                        "name": "SHIP_TO_ADDRESS",
                        "type": "VARCHAR(255)",
                        "description": "Shipping address.",
                        "nullable": True,
                        "is_numeric": False,
                    },
                    {
                        "name": "SHIP_TO_CITY",
                        "type": "VARCHAR(100)",
                        "description": "Shipping city.",
                        "nullable": True,
                        "is_numeric": False,
                    },
                    {
                        "name": "SHIP_TO_COUNTRY",
                        "type": "VARCHAR(100)",
                        "description": "Shipping country.",
                        "nullable": True,
                        "is_numeric": False,
                    },
                    {
                        "name": "PRODUCT_CATEGORY",
                        "type": "VARCHAR(100)",
                        "description": "Product category.",
                        "nullable": True,
                        "is_numeric": False,
                    },
                    {
                        "name": "SALES_REP",
                        "type": "VARCHAR(100)",
                        "description": "Sales representative handling the order.",
                        "nullable": True,
                        "is_numeric": False,
                    },
                    {
                        "name": "CREATED_BY",
                        "type": "VARCHAR(100)",
                        "description": "Email of person who created the order.",
                        "nullable": True,
                        "is_numeric": False,
                    },
                    {
                        "name": "LAST_UPDATED_DATE",
                        "type": "TIMESTAMP",
                        "description": "Timestamp when the order was last modified.",
                        "nullable": True,
                        "is_numeric": False,
                    },
                ],
                "example_queries": [
                    'SELECT ORDER_ID, ORDER_NUMBER, ORDER_DATE, ORDER_STATUS, CUSTOMER_NAME FROM ORDERS WHERE ORDER_ID = 12345;',
                    'SELECT ORDER_ID, ORDER_NUMBER, ORDER_DATE, ORDER_STATUS FROM ORDERS WHERE CUSTOMER_ID = 100 ORDER BY ORDER_DATE DESC LIMIT 100;',
                    'SELECT ORDER_ID, ORDER_NUMBER, ORDER_DATE, ORDER_STATUS, CUSTOMER_NAME FROM ORDERS WHERE CUSTOMER_NAME LIKE \'%Company%\' ORDER BY ORDER_DATE DESC LIMIT 100;',
                    'SELECT COUNT(*) as order_count FROM ORDERS WHERE CUSTOMER_ID = 100;',
                    'SELECT ORDER_ID, ORDER_NUMBER, ORDER_DATE, ORDER_STATUS FROM ORDERS WHERE ORDER_DATE >= \'2024-11-01\' AND ORDER_DATE < \'2024-12-01\' ORDER BY ORDER_DATE DESC LIMIT 100;',
                    'SELECT ORDER_ID, ORDER_NUMBER, ORDER_STATUS, TOTAL_AMOUNT FROM ORDERS WHERE ORDER_STATUS = \'Pending\' LIMIT 100;',
                    'SELECT ORDER_ID, ORDER_NUMBER, PRODUCT_CATEGORY, TOTAL_AMOUNT FROM ORDERS WHERE PRODUCT_CATEGORY = \'Electronics\' LIMIT 100;',
                ],
            }
        ],
        "important_notes": [
            "Always include LIMIT clause to prevent large queries",
            "Use appropriate WHERE clauses for filtering",
            "For date comparisons, use format: ORDER_DATE >= '2024-11-01'",
            "ORDER_ID, CUSTOMER_ID, and TOTAL_AMOUNT are numeric - do NOT use quotes around values",
            "VARCHAR columns require quotes around filter values",
            "Always order results logically (e.g., ORDER BY ORDER_DATE DESC)",
            "Use LIKE for partial text matching (e.g., CUSTOMER_NAME LIKE '%Company%')",
        ],
    }

    # Filter by table names if provided
    if table_names and len(table_names) > 0:
        filtered_tables = [
            t
            for t in schema_info["tables"]
            if any(name.lower() in t["table_name"].lower() for name in table_names)
        ]
        schema_info["tables"] = filtered_tables

    return schema_info


@tool
def get_snowflake_schema(table_names: list[str] | None = None) -> dict[str, Any]:
    """Retrieve mock database schema information for sample tables.

    Returns detailed information about mock table structures, column names,
    data types, and example queries. Use this tool when you need to
    understand the database structure before generating SQL queries.
    Provides schema for specific tables or all available tables.

    This is a mock implementation for testing purposes.

    Args:
        table_names: Optional list of table names to get schema for.
            If not provided or empty, returns schema for all available tables.
            Examples: ['Dimension Order'], ['Order', 'Customer']

    Returns:
        dict[str, Any]: Dictionary containing table schemas and metadata (MOCK DATA)
    """
    try:
        schema_info = _get_schema_info(table_names)

        return {
            "success": True,
            "schema": schema_info,
            "table_count": len(schema_info["tables"]),
        }

    except Exception as e:
        return {
            "success": False,
            "schema": None,
            "table_count": 0,
            "error": str(e),
        }
