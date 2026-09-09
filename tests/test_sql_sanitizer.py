"""
Unit Test: Security Guardrails & SQL AST Sanitizer
Tests that malicious SQL queries (DROP, DELETE, UPDATE, INSERT, ALTER) are strictly blocked.
"""

import pytest
from app.core.guardrails import SecurityGuardrails


def test_allow_valid_select_queries():
    valid_query = "SELECT id, name, email FROM users WHERE tier = 'VIP'"
    is_valid, sanitized = SecurityGuardrails.sanitize_sql(valid_query)
    assert is_valid is True
    assert "LIMIT" in sanitized


def test_block_drop_table_injection():
    malicious_query = "DROP TABLE users; SELECT * FROM orders"
    is_valid, error = SecurityGuardrails.sanitize_sql(malicious_query)
    assert is_valid is False
    assert "Security Violation" in error or "Forbidden SQL operation" in error


def test_block_delete_statement():
    malicious_query = "DELETE FROM orders WHERE id = 1"
    is_valid, error = SecurityGuardrails.sanitize_sql(malicious_query)
    assert is_valid is False
    assert "Security Violation" in error


def test_block_update_statement():
    malicious_query = "UPDATE users SET tier = 'ENTERPRISE' WHERE id = 1"
    is_valid, error = SecurityGuardrails.sanitize_sql(malicious_query)
    assert is_valid is False
    assert "Security Violation" in error


def test_auto_inject_limit():
    query_without_limit = "SELECT * FROM products"
    is_valid, sanitized = SecurityGuardrails.sanitize_sql(query_without_limit, max_limit=50)
    assert is_valid is True
    assert "LIMIT 50" in sanitized
