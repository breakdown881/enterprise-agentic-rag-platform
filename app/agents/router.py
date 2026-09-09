"""
Enterprise Agentic Knowledge Platform (EAKP)
Module: app/agents/router.py
Purpose: Supervisor / Intent Classification & Query Rewriting Node using Pydantic Structured Outputs.
"""

from typing import Dict, Any
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from app.agents.state import GraphState
from app.core.llm_gateway import LLMGateway


# =============================================================================
# 1. PYDANTIC SCHEMA CHO INTENT ROUTING
# =============================================================================
class IntentClassification(BaseModel):
      """
      TODO [Bài tập 1]: Định nghĩa schema Pydantic để ép LLM trả về đúng định dạng:
      1. `intent: str`: Phân loại câu hỏi thành 1 trong 3 giá trị:
         - 'DOCUMENT_RAG': Hỏi chính sách, quy chế, hợp đồng, tài liệu kỹ thuật, SOP.
         - 'TEXT_TO_SQL': Hỏi số liệu định lượng, doanh thu, đơn hàng, người dùng trong cơ sở dữ liệu.
         - 'GENERAL_CHIT_CHAT': Chào hỏi xã giao, cảm ơn, hoặc câu hỏi ngoài lề.
         (Dùng Field(description="...") để hướng dẫn LLM).
      
      2. `rewritten_query: str`: Viết lại câu hỏi thành câu độc lập, rõ nghĩa,
         loại bỏ đại từ mơ hồ và các từ chào hỏi thừa.
      """
      
      intent: str = Field(
          description="Classify the user query into DOCUMENT_RAG, TEXT_TO_SQL, or GENERAL_CHIT_CHAT."
      )
      rewritten_query: str = Field(
          description="Rewrite the user query into a clear standalone search query."
      )


# =============================================================================
# 2. ROUTER AGENT NODE
# =============================================================================
async def router_node(state: GraphState) -> Dict[str, Any]:
      """
      TODO [Bài tập 2]: Triển khai hàm `router_node(state: GraphState)`:
      1. Lấy câu hỏi người dùng: `query = state["user_query"]`.
      2. Lấy Fast Model từ LLMGateway: `llm = LLMGateway.get_fast_model()`.
      3. Ép kiểu output Pydantic: `structured_llm = llm.with_structured_output(IntentClassification)`.
      4. Tạo Prompt phân loại bằng `ChatPromptTemplate.from_messages`:
         - System message: "You are an Enterprise AI Supervisor. Classify the user query into DOCUMENT_RAG, TEXT_TO_SQL, or GENERAL_CHIT_CHAT and rewrite it into a clear standalone search query."
         - Human message: "{query}"
      5. Kết hợp chuỗi: `chain = prompt | structured_llm`.
      6. Chạy bất đồng bộ: `result = await chain.ainvoke({"query": query})`.
      7. Trả về dict cập nhật state:
         {
            "intent": result.intent,
            "rewritten_query": result.rewritten_query
         }
      8. Bọc trong khối try...except để nếu LLM có lỗi mạng thì fallback:
         return {"intent": "DOCUMENT_RAG", "rewritten_query": query}
      """
      try:
         query = state["user_query"]
         llm = LLMGateway.get_fast_model()
         structured_llm = llm.with_structured_output(IntentClassification)
         prompt = ChatPromptTemplate.from_messages([
            ("system", (
               "You are an Enterprise AI Supervisor. Classify the user query into:\n"
               "- DOCUMENT_RAG: Questions about company policies, legal agreements, manuals, SOPs.\n"
               "- TEXT_TO_SQL: Questions requiring quantitative counts, revenue calculations, or DB records.\n"
               "- GENERAL_CHIT_CHAT: Polite greetings or general questions unrelated to company data."
            )),
            ("human", "{query}")
         ])
         chain = prompt | structured_llm
         result: IntentClassification = await chain.ainvoke({"query": query})
         return {
            "intent": result.intent,
            "rewritten_query": result.rewritten_query
         }
      except Exception as e:
         return {
            "intent": "DOCUMENT_RAG",
            "rewritten_query": query
         }
