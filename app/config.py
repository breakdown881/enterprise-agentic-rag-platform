"""
Enterprise Agentic Knowledge Platform (EAKP)
Module: app/config.py
Purpose: Centralized Configuration Management using Pydantic Settings V2.
"""

import json
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application Settings class.
    Automatically loads environment variables from .env file or system environment.
    """

    # =========================================================================
    # 1. APPLICATION CORE SETTINGS
    # =========================================================================
    ENVIRONMENT: str = "development"
    APP_NAME: str = "Enterprise Agentic Knowledge Platform"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "super-secret-dev-key-change-in-production"
    
    # Origins allowed for CORS. Can be a list or a comma-separated / JSON string.
    ALLOWED_ORIGINS: Union[List[str], str] = ["*"]

    # =========================================================================
    # 2. DATABASE SETTINGS (PostgreSQL 16 + pgvector)
    # =========================================================================
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "enterprise_rag"
    
    # TODO [Bài tập 1]: Khai báo DATABASE_URL dạng bất đồng bộ (asyncpg)
    # Ví dụ format: "postgresql+asyncpg://<user>:<password>@<server>:<port>/<db>"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/enterprise_rag"

    # =========================================================================
    # 3. REDIS SETTINGS (Semantic Caching & Rate Limiting)
    # =========================================================================
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Ngưỡng Cosine Similarity để coi 2 câu hỏi là trùng ý nghĩa ngữ nghĩa (0.0 -> 1.0)
    # Tech Lead Tip: Trong doanh nghiệp, nên để >= 0.92 để tránh cache câu trả lời sai
    SEMANTIC_CACHE_THRESHOLD: float = 0.94
    CACHE_TTL_SECONDS: int = 86400  # 24 giờ

    # =========================================================================
    # 4. LLM & EMBEDDING SETTINGS
    # =========================================================================
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    
    DEFAULT_CHAT_MODEL: str = "gpt-4o"
    DEFAULT_FAST_MODEL: str = "gpt-4o-mini"
    DEFAULT_EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    # Số chiều vector của embedding model (text-embedding-3-small là 1536)
    EMBEDDING_DIMENSION: int = 1536

    # =========================================================================
    # 5. RAG & CHUNKING PARAMETERS
    # =========================================================================
    CHUNK_SIZE: int = 800          # Số token / ký tự trung bình cho 1 chunk
    CHUNK_OVERLAP: int = 150       # Độ gối đầu giữa các chunk để không mất ngữ cảnh
    TOP_K_RETRIEVAL: int = 20      # Số lượng candidates lấy ra từ Hybrid Search
    TOP_K_RERANKED: int = 5        # Số lượng documents tinh lọc sau Cross-Encoder
    RERANKER_MODEL: str = "BAAI/bge-reranker-large"

    # =========================================================================
    # 6. LLMOPS & OBSERVABILITY (Langfuse)
    # =========================================================================
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"
    LANGFUSE_ENABLED: bool = False

    # =========================================================================
    # VALIDATORS
    # =========================================================================
    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """
        TODO [Bài tập 2]: Xử lý chuẩn hóa ALLOWED_ORIGINS.
        - Nếu v là string và bắt đầu bằng '[' và kết thúc bằng ']': parse bằng json.loads()
        - Nếu v là string bình thường dạng comma-separated ("http://localhost:3000,http://a.com"):
          hãy split(',') và strip() từng phần tử.
        - Nếu v đã là list: trả về nguyên bản.
        """
        # --- BẠN HÃY TỰ ĐIỀN CODE VÀO ĐÂY ---
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # =========================================================================
    # PYDANTIC CONFIG
    # =========================================================================
    # TODO [Bài tập 3]: Cấu hình SettingsConfigDict cho Pydantic V2:
    # - Đọc file ".env" với encoding utf-8
    # - Bỏ qua các biến thừa trong .env mà không khai báo trong model (extra="ignore")
    # - Phân biệt hoa thường (case_sensitive=True)
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True
    )


# Khởi tạo Singleton instance dùng chung toàn hệ thống
settings = Settings()
