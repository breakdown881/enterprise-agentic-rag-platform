"""
Enterprise Agentic Knowledge Platform (EAKP)
Module: app/agents/state.py
Purpose: Definition of the Global Shared State for LangGraph Multi-Agent Workflow.
"""

from typing import List, Dict, Any, Optional
from typing_extensions import TypedDict


class GraphState(TypedDict):
    """
    TODO [Bài tập 1]: Định nghĩa các trường dữ liệu cho `GraphState`:
    Đây là bộ nhớ dùng chung (Shared Memory) được truyền qua lại giữa tất cả các Agent Nodes trong LangGraph.

    Hãy khai báo đầy đủ các trường sau với Type Annotations chuẩn:
    1. user_query: str                          # Câu hỏi gốc của người dùng
    2. rewritten_query: Optional[str]           # Câu hỏi đã được chuẩn hóa / gỡ bỏ đại từ tham chiếu
    3. intent: Optional[str]                    # 'DOCUMENT_RAG' | 'TEXT_TO_SQL' | 'GENERAL_CHIT_CHAT'
    4. documents: List[Dict[str, Any]]          # Danh sách chunks sau Hybrid Search & Reranking
    5. doc_relevance: Optional[str]             # Kết quả đánh giá của CRAG: 'RELEVANT' | 'IRRELEVANT'
    6. sql_query: Optional[str]                 # Câu lệnh SQL được sinh ra bởi Text-to-SQL Agent
    7. sql_results: Optional[List[Dict[str, Any]]] # Kết quả trả về từ database
    8. sql_error: Optional[str]                 # Thông báo lỗi SQL (nếu có) dùng cho Self-healing loop
    9. sql_retry_count: int                     # Số lần retry sửa câu SQL (giới hạn tối đa 3 lần)
    10. final_response: Optional[str]           # Câu trả lời tổng hợp cuối cùng
    11. citations: List[Dict[str, Any]]         # Danh sách nguồn trích dẫn [Tên file, Trang, Đoạn trích]
    12. requires_fallback: bool                 # Đánh dấu True nếu tài liệu không đủ dữ kiện trả lời
    """
    
    user_query: str 
    rewritten_query: Optional[str]
    intent: Optional[str]
    documents: List[Dict[str, Any]]
    doc_relevance: Optional[str] 
    sql_query: Optional[str]
    sql_results: Optional[List[Dict[str, Any]]]
    sql_error: Optional[str]
    sql_retry_count: int
    final_response: Optional[str]
    citations: List[Dict[str, Any]]
    requires_fallback: bool
