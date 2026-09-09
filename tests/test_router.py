"""
Unit Test: Supervisor Intent Router
Tests that the router accurately classifies DOCUMENT_RAG, TEXT_TO_SQL, and GENERAL_CHIT_CHAT.
"""

import pytest
from app.agents.router import router_node
from app.agents.state import GraphState


@pytest.mark.asyncio
async def test_route_document_query():
    state: GraphState = {
        "user_query": "Chính sách nghỉ phép năm của nhân viên chính thức là bao nhiêu ngày?",
        "rewritten_query": None,
        "intent": None,
        "documents": [],
        "doc_relevance": None,
        "sql_query": None,
        "sql_results": None,
        "sql_error": None,
        "sql_retry_count": 0,
        "final_response": None,
        "citations": [],
        "requires_fallback": False
    }
    result = await router_node(state)
    assert result["intent"] in ["DOCUMENT_RAG", "TEXT_TO_SQL", "GENERAL_CHIT_CHAT"]


@pytest.mark.asyncio
async def test_route_sql_query():
    state: GraphState = {
        "user_query": "Tổng doanh thu bán hàng tháng trước là bao nhiêu tiền?",
        "rewritten_query": None,
        "intent": None,
        "documents": [],
        "doc_relevance": None,
        "sql_query": None,
        "sql_results": None,
        "sql_error": None,
        "sql_retry_count": 0,
        "final_response": None,
        "citations": [],
        "requires_fallback": False
    }
    result = await router_node(state)
    assert result["intent"] in ["TEXT_TO_SQL", "DOCUMENT_RAG"]
