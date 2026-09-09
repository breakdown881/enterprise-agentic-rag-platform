"""
Enterprise Agentic Knowledge Platform (EAKP)
Module: app/agents/synthesizer.py
Purpose: Synthesizer & Citation Verifier Agent - Grounded Response Generation with Transparent Citations.
"""

from typing import Dict, Any, List
from urllib import response
from langchain_core.prompts import ChatPromptTemplate
from app.agents.state import GraphState
from app.core.llm_gateway import LLMGateway


async def synthesizer_node(state: GraphState) -> Dict[str, Any]:
    """
    TODO [Bài tập 1]: Triển khai hàm `synthesizer_node(state: GraphState)`:
    Hàm này tổng hợp kết quả cuối cùng từ các Agent trước đó:

    1. Lấy thông tin từ state:
       - query = state.get("rewritten_query") or state["user_query"]
       - intent = state.get("intent", "DOCUMENT_RAG")
       - requires_fallback = state.get("requires_fallback", False)
       - documents = state.get("documents", [])
       - sql_results = state.get("sql_results", [])
       - sql_query = state.get("sql_query", "")

    2. Nhánh 1 - XỬ LÝ FALLBACK (Nếu CRAG đánh giá tài liệu không liên quan):
       if requires_fallback:
           return {
               "final_response": (
                   "Xin lỗi, hiện tại cơ sở tri thức nội bộ của hệ thống không chứa thông tin "
                   "đầy đủ để trả lời câu hỏi này. Bạn vui lòng liên hệ bộ phận liên quan để được hỗ trợ."
               ),
               "citations": []
           }

    3. Nhánh 2 - XỬ LÝ TEXT-TO-SQL:
       if intent == "TEXT_TO_SQL":
           - Tạo prompt yêu cầu LLM tóm tắt bảng dữ liệu `sql_results` thành phân tích kinh doanh rõ ràng.
           - Gọi LLM (`LLMGateway.get_chat_model()`).
           - Citations trả về dạng:
             citations = [{"source": "PostgreSQL Database", "query": sql_query, "record_count": len(sql_results)}]
           - Trả về: {"final_response": response.content, "citations": citations}

    4. Nhánh 3 - XỬ LÝ DOCUMENT RAG:
       - Tạo context từ các chunks:
         context_text = "\n\n".join([f"--- Đoạn {i+1} (Nguồn: {d['metadata'].get('source')}, Trang {d['metadata'].get('page_number')}):\n{d['content']}" for i, d in enumerate(documents)])
       - Tạo prompt nghiêm ngặt:
         System: "You are a professional Enterprise Copilot. Answer the query truthfully based strictly on the provided context. Include inline source markers like [Nguồn, Trang]."
         Human: "Query: {query}\n\nContext:\n{context}"
       - Gọi LLM và lấy `response.content`.
       - Tạo danh sách citations:
         citations = [
             {
                 "source": doc["metadata"].get("source", "Unknown"),
                 "page_number": doc["metadata"].get("page_number", 1),
                 "snippet": doc["content"][:200]
             }
             for doc in documents[:5]
         ]
       - Trả về: {"final_response": response.content, "citations": citations}
    """
    
    if state.get("requires_fallback"):
      return {
          "final_response": "Xin lỗi, hiện tại cơ sở tri thức nội bộ chưa có thông tin đầy đủ để giải đáp vấn đề này của bạn. Vui lòng liên hệ bộ phận liên quan để được hỗ trợ.",
          "citations": []
      }
      
    if state.get("intent") == "TEXT_TO_SQL":
      sql_results = state.get("sql_results", [])
      sql_query = state.get("sql_query", "")
      prompt = ChatPromptTemplate.from_messages([
          ("system", "You are a Business Intelligence Analyst. Synthesize the SQL query results into a clear, executive-level summary. Present key numbers clearly."),
          ("human", "Question: {query}\nSQL Executed: {sql}\nQuery Results: {results}")
      ])
      llm = LLMGateway.get_chat_model(temperature=0.0)
      response = await (prompt | llm).ainvoke({
          "query": state.get("rewritten_query") or state["user_query"],
          "sql": sql_query,
          "results": str(sql_results)
      })
      citations = [{"source": "PostgreSQL Database", "query": sql_query, "record_count": len(sql_results)}]
      return {"final_response": response.content, "citations": citations}
    
    if state.get("intent") == "DOCUMENT_RAG":
      documents = state.get("documents", [])
      context_text = "\n\n".join([
          f"--- Đoạn {i+1} (File: {d['metadata'].get('source')}, Trang: {d['metadata'].get('page_number')}):\n{d['content']}"
          for i, d in enumerate(documents)
      ])
      
      prompt = ChatPromptTemplate.from_messages([
          ("system", "You are an Enterprise Knowledge Assistant. Answer the question truthfully and accurately based strictly on the provided context. Always cite your sources [File, Page]."),
          ("human", "Question: {query}\n\nContext:\n{context}")
      ])
      llm = LLMGateway.get_chat_model(temperature=0.0)
      response = await (prompt | llm).ainvoke({"query": state.get("user_query"), "context": context_text})
      citations = [
          {
              "source": doc["metadata"].get("source", "Unknown"),
              "page_number": doc["metadata"].get("page_number", 1),
              "snippet": doc["content"][:200]
          }
          for doc in documents[:5]
      ]
      return {"final_response": response.content, "citations": citations}
      
    # Nhánh mặc định: Chào hỏi / trò chuyện thông thường
    llm = LLMGateway.get_fast_model()
    chat_resp = await llm.ainvoke(state.get("user_query"))
    return {"final_response": chat_resp.content, "citations": []}
