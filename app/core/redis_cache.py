"""
Enterprise Agentic Knowledge Platform (EAKP)
Module: app/core/redis_cache.py
Purpose: Semantic Caching Client using Redis to reduce Token Cost and deliver Sub-50ms Latency.
"""

import hashlib
import json
from typing import Optional, Dict, Any, List
import numpy as np
import redis.asyncio as aioredis
from loguru import logger
from app.config import settings
from app.core.llm_gateway import LLMGateway


class SemanticCacheManager:
    """
    Manages Semantic Vector Caching in Redis.
    Matches incoming user queries against previously answered queries using Cosine Similarity.
    """

    def __init__(self):
        self.redis_url = settings.REDIS_URL
        self.client: Optional[aioredis.Redis] = None
        self.threshold = settings.SEMANTIC_CACHE_THRESHOLD
        self.ttl = settings.CACHE_TTL_SECONDS
        self.embedding_model = None

    async def connect(self):
        """Khởi tạo kết nối Redis client"""
        if not self.client:
            try:
                self.client = aioredis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                await self.client.ping()
                self.embedding_model = LLMGateway.get_embedding_model()
                logger.info("Connected to Redis semantic cache successfully.")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}. Semantic cache will operate in bypass mode.")
                self.client = None

    async def close(self):
        """Đóng kết nối Redis"""
        if self.client:
            await self.client.close()

    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Helper: Tính Cosine Similarity giữa 2 vector bằng numpy"""
        a = np.array(vec1)
        b = np.array(vec2)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    async def get(self, query: str) -> Optional[Dict[str, Any]]:
        """
        TODO [Bài tập 1]: Triển khai hàm kiểm tra Semantic Cache:
        1. Nếu `not self.client`: return None (Bypass mode).
        2. Bọc trong khối try...except:
           - Tính embedding của câu hỏi mới:
             `query_vec = await self.embedding_model.aembed_query(query)`
           - Lấy tất cả các cache keys có tiền tố 'semantic_cache:*':
             `keys = await self.client.keys("semantic_cache:*")`
           - Duyệt qua từng key:
             + Lấy dữ liệu dạng JSON: `raw_data = await self.client.get(key)`
             + Parse `data = json.loads(raw_data)`
             + Lấy vector đã lưu: `cached_vec = data["embedding"]`
             + Tính điểm: `sim = self._cosine_similarity(query_vec, cached_vec)`
             + Nếu `sim >= self.threshold`:
               Log: `logger.info(f"Semantic Cache Hit! Similarity: {sim:.4f}")`
               Return:
               {
                   "answer": data["answer"],
                   "citations": data["citations"],
                   "cached": True,
                   "similarity": sim
               }
        3. Nếu không tìm thấy key nào vượt ngưỡng threshold: return None (Cache Miss).
        4. Nếu có Exception: log warning và return None.
        """
        if not self.client: 
            return None
        
        try:
            query_vec = await self.embedding_model.aembed_query(query)
            keys = await self.client.keys("semantic_cache:*")
            for key in keys:
                raw_data = await self.client.get(key)
                data = json.loads(raw_data)
                sim = self._cosine_similarity(query_vec, data["embedding"])
                if sim >= self.threshold:
                    logger.info(f"Semantic Cache Hit! Similarity: {sim:.4f}")
                    return {
                        "answer": data["answer"],
                        "citations": data["citations"],
                        "cached": True,
                        "similarity": sim
                    }
            return None  # Cache Miss
        except Exception as e:
            logger.warning(f"Failed to embed query: {e}")
            return None

    async def set(self, query: str, answer: str, citations: List[Dict[str, Any]]) -> bool:
        """
        TODO [Bài tập 2]: Lưu câu trả lời vào Semantic Cache:
        1. Nếu `not self.client`: return False.
        2. Bọc trong khối try...except:
           - Tính embedding của query:
             `query_vec = await self.embedding_model.aembed_query(query)`
           - Tạo cache key duy nhất dựa trên hash hoặc timestamp:
             `import hashlib; key = f"semantic_cache:{hashlib.sha256(query.encode()).hexdigest()[:16]}"`
           - Tạo payload dict:
             payload = {
                 "query": query,
                 "answer": answer,
                 "citations": citations,
                 "embedding": query_vec
             }
           - Lưu vào Redis kèm TTL:
             `await self.client.setex(key, self.ttl, json.dumps(payload))`
           - Log: `logger.info(f"Saved query to semantic cache: '{query[:40]}...'")`
           - return True
        3. Nếu có Exception: log warning và return False.
        """
        if not self.client: 
            return False
        
        try:
            query_vec = await self.embedding_model.aembed_query(query)
            
            import hashlib
            key = f"semantic_cache:{hashlib.sha256(query.encode()).hexdigest()[:16]}"
            
            payload = {
                "query": query,
                "answer": answer,
                "citations": citations,
                "embedding": query_vec
            }
            await self.client.setex(key, self.ttl, json.dumps(payload))
            logger.info(f"Saved query to semantic cache: '{query[:40]}...'")
            return True
        except Exception as e:
            logger.warning(f"Failed to save query to semantic cache: {e}")
            return False


# Khởi tạo Singleton instance
cache_manager = SemanticCacheManager()
