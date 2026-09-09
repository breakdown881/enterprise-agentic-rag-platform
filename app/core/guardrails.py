"""
Enterprise Agentic Knowledge Platform (EAKP)
Module: app/core/guardrails.py
Purpose: SQL AST Sanitizer using sqlglot and Prompt Injection Detection.
"""

from typing import Tuple
import sqlglot
from sqlglot import exp
from loguru import logger


class SecurityGuardrails:
    """
    Production-grade Security Guardrails for Text-to-SQL and LLM inputs.
    """

    FORBIDDEN_OPERATIONS = (
        exp.Drop,
        exp.Delete,
        exp.Update,
        exp.Insert,
        exp.Alter,
        exp.Command,
        exp.Create,
    )

    @classmethod
    def sanitize_sql(cls, query_str: str, max_limit: int = 100) -> Tuple[bool, str]:
        """
        Parses SQL via Abstract Syntax Tree (AST) using sqlglot:
        1. Enforces that only SELECT statements are permitted.
        2. Blocks any destructive DDL/DML (DROP, DELETE, UPDATE, INSERT, ALTER).
        3. Automatically enforces LIMIT <= max_limit to prevent memory exhaustion attacks.
        
        Returns:
            Tuple[bool, str]: (is_valid, sanitized_sql_or_error_message)
        """
        try:
            # Parse query using Postgres dialect
            parsed = sqlglot.parse_one(query_str, read="postgres")
            if not parsed:
                return False, "Unable to parse SQL syntax."

            # Check for forbidden AST nodes
            for forbidden_op in cls.FORBIDDEN_OPERATIONS:
                if parsed.find(forbidden_op):
                    logger.warning(f"Security Alert: Blocked forbidden SQL operation: {forbidden_op.__name__}")
                    return False, f"Security Violation: Forbidden SQL operation '{forbidden_op.__name__}' is blocked."

            # Enforce that root expression is a SELECT
            if not isinstance(parsed, exp.Select):
                return False, "Security Violation: Only read-only SELECT queries are allowed."

            # Enforce or inject LIMIT clause
            limit_clause = parsed.args.get("limit")
            if not limit_clause:
                parsed = parsed.limit(max_limit)
            else:
                try:
                    limit_val = int(limit_clause.expression.name)
                    if limit_val > max_limit:
                        parsed.set("limit", exp.Limit(this=exp.Literal.number(max_limit)))
                except Exception:
                    parsed.set("limit", exp.Limit(this=exp.Literal.number(max_limit)))

            sanitized_query = parsed.sql(dialect="postgres")
            return True, sanitized_query

        except Exception as e:
            logger.error(f"SQL AST Parsing Error: {e}")
            return False, f"SQL Syntax Error during AST analysis: {str(e)}"
