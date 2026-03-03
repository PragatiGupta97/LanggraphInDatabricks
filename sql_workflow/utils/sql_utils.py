"""SQL Utility Functions.

Helper functions for SQL query processing and cleaning.
"""

import re


def clean_sql_query(sql_text: str) -> str:
    """Extract and clean SQL query from markdown/comments.

    Removes:
    - Markdown code fences (```sql, ```)
    - Comment-only lines (starting with --)
    - Inline comments (after -- on same line)

    Args:
        sql_text: Raw SQL text potentially containing markdown or comments

    Returns:
        Cleaned SQL query string
    """
    # Remove markdown code fences
    sql_text = re.sub(r"```sql\s*", "", sql_text)
    sql_text = re.sub(r"```\s*", "", sql_text)

    # Split by lines and remove comment lines
    lines = sql_text.split("\n")
    cleaned_lines = []

    for line in lines:
        # Skip lines that are only comments
        stripped = line.strip()
        if stripped.startswith("--"):
            continue

        # Remove inline comments
        if "--" in line:
            line = line.split("--")[0]

        if stripped:
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()
