"""
Enterprise Agentic Knowledge Platform (EAKP)
Module: app/agents/workflow.py
Purpose: Compilation of the Full Multi-Agent StateGraph with Conditional Edges & Cycles.
"""

from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, START, END
from app.config import settings
from app.core.database import AsyncSessionLocal
from app.retrieval.hybrid_search import HybridSearchEngine
from app.retrieval.reranker import CrossEncoderReranker

from app.agents.state import GraphState
from app.agents.router import router_node
from app.agents.crag_agent import grade_documents_node
from app.agents.text_to_sql_agent import generate_sql_node, execute_sql_node
from app.agents.synthesizer import synthesizer_node


# =============================================================================
# 1. RETRIEVAL INTERFACE NODE
# =============================================================================
async def retrieval_node(state: GraphState) -> Dict[str, Any]:
    """
    Retrieval Node:
    Calls HybridSearchEngine (pgvector + tsvector + RRF) and passes candidates to CrossEncoderReranker.
    """
    query = state.get("rewritten_query") or state["user_query"]
    
    async with AsyncSessionLocal() as session:
        search_engine = HybridSearchEngine(session)
        raw_docs = await search_engine.search(query, top_k=settings.TOP_K_RETRIEVAL)
        
    reranker = CrossEncoderReranker()
    reranked_docs = reranker.rerank(query, raw_docs, top_n=settings.TOP_K_RERANKED)
    return {"documents": reranked_docs}


# =============================================================================
# 2. ROUTING & CONDITIONAL EDGE FUNCTIONS
# =============================================================================
def route_intent_edge(state: GraphState) -> Literal["retrieval", "generate_sql", "synthesizer"]:
    """
    TODO [Bài tập 1]: Điều hướng luồng sau khi Supervisor Router phân loại intent:
    - Nếu state.get("intent") == "DOCUMENT_RAG": trả về "retrieval"
    - Nếu state.get("intent") == "TEXT_TO_SQL": trả về "generate_sql"
    - Ngược lại (GENERAL_CHIT_CHAT): trả về "synthesizer"
    """
    intent = state.get("intent")
    if intent == "DOCUMENT_RAG":
        return "retrieval"
    elif intent == "TEXT_TO_SQL":
        return "generate_sql"
    else:
        return "synthesizer"


def sql_self_healing_edge(state: GraphState) -> Literal["generate_sql", "synthesizer"]:
    """
    TODO [Bài tập 2]: Vòng lặp tự sửa lỗi Self-Healing cho Text-to-SQL:
    - Lấy `sql_error = state.get("sql_error")`
    - Lấy `retry_count = state.get("sql_retry_count", 0)`
    - Nếu CÓ `sql_error` và `retry_count < 3`:
      Trả về "generate_sql" để LLM tiếp tục sửa lại câu SQL!
    - Ngược lại (thành công hoặc đã hết 3 lần thử):
      Trả về "synthesizer" để tổng hợp kết quả ra màn hình.
    """
    sql_error = state.get("sql_error")
    retry_count = state.get("sql_retry_count", 0)
    
    if sql_error and retry_count < 3:
        return "generate_sql"
    else:
        return "synthesizer"


# =============================================================================
# 3. BUILD & COMPILE STATEGRAPH
# =============================================================================
def create_agent_graph():
    """
    TODO [Bài tập 3]: Lắp ghép toàn bộ StateGraph:
    1. Khởi tạo `workflow = StateGraph(GraphState)`
    2. Thêm các Node bằng `workflow.add_node(...)`:
       - "router": router_node
       - "retrieval": retrieval_node
       - "grade_docs": grade_documents_node
       - "generate_sql": generate_sql_node
       - "execute_sql": execute_sql_node
       - "synthesizer": synthesizer_node

    3. Thêm các Edges (cố định và có điều kiện):
       - workflow.add_edge(START, "router")
       - workflow.add_conditional_edges("router", route_intent_edge)
       - workflow.add_edge("retrieval", "grade_docs")
       - workflow.add_edge("grade_docs", "synthesizer")
       - workflow.add_edge("generate_sql", "execute_sql")
       - workflow.add_conditional_edges("execute_sql", sql_self_healing_edge)
       - workflow.add_edge("synthesizer", END)

    4. Biên dịch đồ thị: `return workflow.compile()`
    """
    workflow = StateGraph(GraphState)
    workflow.add_node("router", router_node)
    workflow.add_node("retrieval", retrieval_node)
    workflow.add_node("grade_docs", grade_documents_node)
    workflow.add_node("generate_sql", generate_sql_node)
    workflow.add_node("execute_sql", execute_sql_node)
    workflow.add_node("synthesizer", synthesizer_node)
    
    workflow.add_edge(START, "router")
    workflow.add_conditional_edges("router", route_intent_edge)
    
    workflow.add_edge("retrieval", "grade_docs")
    workflow.add_edge("grade_docs", "synthesizer")
    
    workflow.add_edge("generate_sql", "execute_sql")
    workflow.add_conditional_edges("execute_sql", sql_self_healing_edge)
    
    workflow.add_edge("synthesizer", END)
    
    return workflow.compile()


# Khởi tạo instance đồ thị hoàn chỉnh dùng chung
app_graph = create_agent_graph()
