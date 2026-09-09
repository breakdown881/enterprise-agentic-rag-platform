"""
Enterprise Agentic Knowledge Platform (EAKP)
Module: app/agents/crag_agent.py
Purpose: Corrective RAG (CRAG) Document Grader Node to eliminate Hallucinations.
"""

from typing import Dict, Any
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from app.agents.state import GraphState
from app.core.llm_gateway import LLMGateway


# =============================================================================
# 1. PYDANTIC SCHEMA CHO DOCUMENT GRADER
# =============================================================================
class DocumentGrade(BaseModel):
    """
    TODO [Bài tập 1]: Định nghĩa schema kiểm tra mức độ liên quan của tài liệu:
    - binary_score: str = Field(description="Chấm điểm nhị phân xem tài liệu có chứa dữ kiện trả lời câu hỏi không: 'yes' hoặc 'no'")
    """
    binary_score: str = Field(description="Binary score 'yes' or 'no' indicating if the document is relevant to the query")


# =============================================================================
# 2. CRAG DOCUMENT GRADER NODE
# =============================================================================
async def grade_documents_node(state: GraphState) -> Dict[str, Any]:
      """
      TODO [Bài tập 2]: Triển khai hàm `grade_documents_node(state: GraphState)`:
      1. Lấy câu hỏi: `query = state.get("rewritten_query") or state["user_query"]`.
      2. Lấy danh sách tài liệu từ state: `docs = state.get("documents", [])`.
      3. Nếu `not docs`: Không tìm thấy tài liệu nào, trả về:
         return {"doc_relevance": "IRRELEVANT", "requires_fallback": True}

      4. Khởi tạo Fast Model và ép kiểu Pydantic:
         llm = LLMGateway.get_fast_model()
         structured_llm = llm.with_structured_output(DocumentGrade)

      5. Ghép nội dung của top 3 chunks lại làm context:
         context = "\n\n".join([d["content"] for d in docs[:3]])

      6. Tạo Prompt đánh giá:
         - System: "You are an expert evaluator assessing whether the retrieved context contains factual information to answer the user query. Grade with a binary score 'yes' or 'no'."
         - Human: "User Query: {query}\n\nContext:\n{context}"

      7. Chạy chain: `grade: DocumentGrade = await (prompt | structured_llm).ainvoke({"query": query, "context": context})`
      8. Kiểm tra kết quả:
         is_relevant = (grade.binary_score.lower() == "yes")
         return {
            "doc_relevance": "RELEVANT" if is_relevant else "IRRELEVANT",
            "requires_fallback": not is_relevant
         }
      9. Bọc trong try...except: nếu có lỗi thì fallback về `{"doc_relevance": "RELEVANT", "requires_fallback": False}`.
      """
      query = state.get("rewritten_query") or state["user_query"]
      docs = state.get("documents", [])
      if not docs:
         return {"doc_relevance": "IRRELEVANT", "requires_fallback": True}

      try:
         llm = LLMGateway.get_fast_model()
         structured_llm = llm.with_structured_output(DocumentGrade)
         context = "\n\n".join([d["content"] for d in docs[:3]])
         prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert evaluator assessing whether the retrieved context contains factual information to answer the user query. Grade with a binary score 'yes' or 'no'."),
            ("human", "User Query: {query}\n\nContext:\n{context}")
         ])
         
         grade: DocumentGrade = await (prompt | structured_llm).ainvoke({"query": query, "context": context})
         is_relevant = (grade.binary_score.lower() == "yes")
         return {
            "doc_relevance": "RELEVANT" if is_relevant else "IRRELEVANT",
            "requires_fallback": not is_relevant
         }
      except Exception as e:
         return {"doc_relevance": "RELEVANT", "requires_fallback": False}
         
