"""
Enterprise Agentic Knowledge Platform (EAKP)
Module: app/retrieval/hybrid_search.py
Purpose: Hybrid Search Engine combining pgvector Dense Search and tsvector Sparse Search with RRF.
"""

from typing import List, Dict, Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.core.llm_gateway import LLMGateway
from app.retrieval.rrf_fusion import ReciprocalRankFusion


class HybridSearchEngine:
    """
    Executes hybrid retrieval by querying PostgreSQL for both semantic similarity
    (pgvector cosine distance) and keyword relevance (tsvector full-text search),
    then fusing their rankings via Reciprocal Rank Fusion.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.embedding_model = LLMGateway.get_embedding_model()

    async def search(
        self,
        query: str,
        top_k: int = settings.TOP_K_RETRIEVAL
    ) -> List[Dict[str, Any]]:
         """
         TODO [Bài tập 1]: Triển khai Hybrid Search kết hợp:
         1. Tạo vector embedding cho câu hỏi:
            `query_embedding = await self.embedding_model.aembed_query(query)`

         2. Chuẩn bị câu SQL Dense Vector Search:
            SELECT id, doc_id, doc_title, content, metadata,
                     1 - (embedding <=> :query_embedding) AS similarity
            FROM document_chunks
            ORDER BY embedding <=> :query_embedding ASC
            LIMIT :limit

         3. Chuẩn bị câu SQL Sparse Full-text Search:
            SELECT id, doc_id, doc_title, content, metadata,
                     ts_rank_cd(tsv, plainto_tsquery('english', :query)) AS rank
            FROM document_chunks
            WHERE tsv @@ plainto_tsquery('english', :query)
            ORDER BY rank DESC
            LIMIT :limit

         4. Thực thi cả 2 câu truy vấn qua `self.session.execute(...)`:
            - dense_res = await self.session.execute(dense_sql, {"query_embedding": str(query_embedding), "limit": top_k})
            - dense_rows = [dict(row._mapping) for row in dense_res.fetchall()]

            - sparse_res = await self.session.execute(sparse_sql, {"query": query, "limit": top_k})
            - sparse_rows = [dict(row._mapping) for row in sparse_res.fetchall()]

         5. Hòa trộn kết quả qua RRF:
            `fused_results = ReciprocalRankFusion.fuse(dense_rows, sparse_rows)`

         6. Trả về `top_k` phần tử đầu tiên: `return fused_results[:top_k]`.
         """
        
         query_embedding = await self.embedding_model.aembed_query(query)
         dense_sql = text("""
            SELECT id, doc_id, doc_title, content, metadata,
                  1 - (embedding <=> :query_embedding) AS similarity
            FROM document_chunks
            ORDER BY embedding <=> :query_embedding ASC
            LIMIT :limit
         """)
         
         sparse_sql = text("""
            SELECT id, doc_id, doc_title, content, metadata,
                  ts_rank_cd(tsv, plainto_tsquery('english', :query)) AS rank
            FROM document_chunks
            WHERE tsv @@ plainto_tsquery('english', :query)
            ORDER BY rank DESC
            LIMIT :limit
         """)
         
         dense_res = await self.session.execute(dense_sql, {"query_embedding": str(query_embedding), "limit": top_k})
         dense_rows = [dict(row._mapping) for row in dense_res.fetchall()]
         sparse_res = await self.session.execute(sparse_sql, {"query": query, "limit": top_k})
         sparse_rows = [dict(row._mapping) for row in sparse_res.fetchall()]
         
         fused_results = ReciprocalRankFusion.fuse(dense_rows, sparse_rows)
         return fused_results[:top_k]
