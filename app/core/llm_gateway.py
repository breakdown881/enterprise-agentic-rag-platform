"""
Enterprise Agentic Knowledge Platform (EAKP)
Module: app/core/llm_gateway.py
Purpose: Centralized Model Gateway for LLMs and Embedding Models with fallback and tracing.
"""

from typing import Optional
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from app.config import settings


class LLMGateway:
    """
    Centralized Gateway for Large Language Models and Embedding Models.
    Ensures consistent parameter configuration, API keys, and temperature settings across agents.
    """

    @classmethod
    def get_chat_model(
        cls,
        model_name: Optional[str] = None,
        temperature: float = 0.0,
        streaming: bool = False
    ) -> ChatOpenAI:
        """
        TODO [Bài tập 1]: Khởi tạo và trả về instance `ChatOpenAI`:
        - model: Sử dụng `model_name` nếu được truyền vào, nếu không thì lấy mặc định `settings.DEFAULT_CHAT_MODEL`
        - api_key: Lấy từ `settings.OPENAI_API_KEY`
        - temperature: Truyền vào giá trị `temperature` (mặc định 0.0 để output có tính xác định cao, ít ảo giác)
        - streaming: Truyền vào cờ `streaming` (dùng cho Server-Sent Events sau này)
        """
        mode = model_name if model_name else settings.DEFAULT_CHAT_MODEL
        return ChatOpenAI(
            model_name=mode,
            api_key=settings.OPENAI_API_KEY,
            temperature=temperature,
            streaming=streaming
        )

    @classmethod
    def get_fast_model(cls, temperature: float = 0.0) -> ChatOpenAI:
        """
        TODO [Bài tập 2]: Khởi tạo mô hình gọn nhẹ, tốc độ cao (Fast / Small Model):
        - Dùng cho các tác vụ như Router phân loại intent, Document Grader trong CRAG, hoặc Query Rewriting.
        - Gọi lại `cls.get_chat_model()` với model là `settings.DEFAULT_FAST_MODEL` (gpt-4o-mini).
        """
        return cls.get_chat_model(
            model_name=settings.DEFAULT_FAST_MODEL,
            temperature=temperature
        )

    @classmethod
    def get_embedding_model(cls) -> OpenAIEmbeddings:
        """
        TODO [Bài tập 3]: Khởi tạo và trả về instance `OpenAIEmbeddings`:
        - model: Lấy từ `settings.DEFAULT_EMBEDDING_MODEL` (text-embedding-3-small)
        - api_key: Lấy từ `settings.OPENAI_API_KEY`
        - dimensions: Lấy từ `settings.EMBEDDING_DIMENSION` (1536 chiều)
        """
        return OpenAIEmbeddings(
            model=settings.DEFAULT_EMBEDDING_MODEL,
            api_key=settings.OPENAI_API_KEY,
            dimensions=settings.EMBEDDING_DIMENSION
        )
