"""
Enterprise Agentic Knowledge Platform (EAKP)
Module: app/api/v1/chat.py
Purpose: Server-Sent Events (SSE) Streaming Chat Endpoint with Semantic Cache Interception.
"""

import json
from typing import AsyncGenerator
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from app.core.guardrails import SecurityGuardrails
from app.core.redis_cache import cache_manager
from app.agents.workflow import app_graph


router = APIRouter(prefix="/chat", tags=["Chat & Streaming"])


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000, description="User question / prompt")


async def chat_event_generator(query: str) -> AsyncGenerator[str, None]:
    """
    TODO [Bài tập 1]: Triển khai Generator truyền dữ liệu thời gian thực (SSE):
    1. Bước 1 - Kiểm tra Prompt Injection:
       if SecurityGuardrails.detect_prompt_injection(query):
           yield json.dumps({"event": "error", "data": "Security Alert: Prompt injection pattern detected."})
           return

    2. Bước 2 - Kiểm tra Semantic Cache (Tối ưu hóa độ trễ & chi phí):
       cached_result = await cache_manager.get(query)
       if cached_result:
           # Trả về tín hiệu bắt đầu
           yield json.dumps({"event": "status", "data": "Hit Semantic Cache! (Zero token cost, ~30ms)"})
           # Trả về toàn bộ câu trả lời từ cache
           yield json.dumps({"event": "message", "data": cached_result["answer"]})
           # Trả về citations
           yield json.dumps({"event": "citations", "data": cached_result["citations"]})
           yield json.dumps({"event": "done", "data": "[DONE]"})
           return

    3. Bước 3 - Cache Miss: Kích hoạt Multi-Agent Workflow (LangGraph):
       yield json.dumps({"event": "status", "data": "Analyzing intent & searching knowledge base..."})

       # Chạy đồ thị LangGraph
       initial_state = {
           "user_query": query,
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

       final_state = await app_graph.ainvoke(initial_state)

       answer = final_state.get("final_response", "Không thể sinh câu trả lời.")
       citations = final_state.get("citations", [])

       # Lưu câu trả lời chất lượng vào Semantic Cache cho người sau
       if not final_state.get("requires_fallback"):
           await cache_manager.set(query, answer, citations)

       # Gửi thông điệp hoàn thành tới người dùng
       yield json.dumps({"event": "message", "data": answer})
       yield json.dumps({"event": "citations", "data": citations})
       yield json.dumps({"event": "done", "data": "[DONE]"})
    """
    if SecurityGuardrails.detect_prompt_injection(query):
        yield json.dumps({"event": "error", "data": "Security Alert: Prompt injection pattern detected."})
        return
    
    cached_result = await cache_manager.get(query)
    if cached_result:
        yield json.dumps({"event": "status", "data": "Hit Semantic Cache! (Sub-50ms latency, zero token cost)"})
        yield json.dumps({"event": "message", "data": cached_result["answer"]})
        yield json.dumps({"event": "citations", "data": cached_result["citations"]})
        yield json.dumps({"event": "done", "data": "[DONE]"})
        return
    
    yield json.dumps({"event": "status", "data": "Orchestrating multi-agent knowledge workflow..."})
    initial_state = {
        "user_query": query,
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
    final_state = await app_graph.ainvoke(initial_state)
    answer = final_state.get("final_response", "Không thể sinh câu trả lời.")
    citations = final_state.get("citations", [])
    # Lưu vào cache nếu câu trả lời không phải là fallback
    if not final_state.get("requires_fallback"):
        await cache_manager.set(query, answer, citations)
    yield json.dumps({"event": "message", "data": answer})
    yield json.dumps({"event": "citations", "data": citations})
    yield json.dumps({"event": "done", "data": "[DONE]"})


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """
    TODO [Bài tập 2]: Triển khai Endpoint trả về Server-Sent Events (SSE):
    - Trả về instance của `EventSourceResponse(chat_event_generator(request.query))`
    """
    return EventSourceResponse(chat_event_generator(request.query))
