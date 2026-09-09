"""
Enterprise Agentic Knowledge Platform (EAKP)
Module: app/ingestion/vector_store.py
Purpose: Asynchronous pgvector Store Manager with Batch Embedding Upsert.
"""

import json
from typing import List, Dict, Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from app.core.llm_gateway import LLMGateway


class PostgresVectorStore:
    """
    Manages vector storage and indexing within PostgreSQL using the pgvector extension.
    Coordinates embedding generation and transactional database upserts.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.embedding_model = LLMGateway.get_embedding_model()

    async def upsert_chunks(
        self,
        chunks: List[Dict[str, Any]],
        doc_title: str
    ) -> int:
        """
        TODO [Bài tập 1]: Nạp danh sách chunks vào PostgreSQL với pgvector:
        1. Kiểm tra nếu `chunks` rỗng thì `return 0`.
        2. Gom tất cả nội dung text cần embed:
           `texts_to_embed = [c["content"] for c in chunks]`
        3. Tạo embeddings bất đồng bộ cho toàn bộ danh sách text bằng:
           `embeddings = await self.embedding_model.aembed_documents(texts_to_embed)`
        4. Chuẩn bị câu lệnh SQL chèn dữ liệu bằng SQLAlchemy `text(...)`:
           INSERT INTO document_chunks (doc_id, doc_title, content, metadata, embedding)
           VALUES (:doc_id, :doc_title, :content, :metadata::jsonb, :embedding)
        5. Lặp qua từng cặp `(chunk, embedding)` bằng `zip(chunks, embeddings)`:
           Thực thi câu SQL với tham số:
           - "doc_id": chunk["doc_id"]
           - "doc_title": doc_title
           - "content": chunk["content"]
           - "metadata": json.dumps(chunk["metadata"])
           - "embedding": str(embedding)  # pgvector nhận chuỗi dạng "[0.012, -0.043, ...]"
        6. Commit transaction: `await self.session.commit()`.
        7. Log thành công bằng `logger.info(...)` và trả về số lượng chunks đã insert (`len(chunks)`).
        """
        if not chunks:
            return 0
        
        texts_to_embed = [c["content"] for c in chunks]
        embeddings = await self.embedding_model.aembed_documents(texts_to_embed)
        stmt = text("""
            INSERT INTO document_chunks (doc_id, doc_title, content, metadata, embedding)
            VALUES (:doc_id, :doc_title, :content, :metadata::jsonb, :embedding)
        """)
        for chunk, embedding in zip(chunks, embeddings):
            await self.session.execute(stmt, {
                "doc_id": chunk["doc_id"],
                "doc_title": doc_title,
                "content": chunk["content"],
                "metadata": json.dumps(chunk["metadata"]),
                "embedding": str(embedding)
            })
        await self.session.commit()
        logger.info(f"Inserted {len(chunks)} chunks for document '{doc_title}' (doc_id={chunks[0]['doc_id']})")
        return len(chunks)

    async def delete_document(self, doc_id: str) -> int:
        """
        TODO [Bài tập 2]: Xóa tất cả các chunk thuộc về một `doc_id`:
        - Chuẩn bị câu lệnh: DELETE FROM document_chunks WHERE doc_id = :doc_id
        - Thực thi câu lệnh qua `self.session.execute(...)`
        - Commit transaction qua `self.session.commit()`
        - Trả về số lượng bản ghi đã xóa (nếu có thể) hoặc 1.
        """
        stmt = text("DELETE FROM document_chunks WHERE doc_id = :doc_id")
        await self.session.execute(stmt, {"doc_id": doc_id})
        await self.session.commit()
        return 1
