"""
Enterprise Agentic Knowledge Platform (EAKP)
Module: app/retrieval/reranker.py
Purpose: Cross-Encoder Re-ranking using BAAI/bge-reranker-large with Graceful Fallback.
"""

from typing import List, Dict, Any
from loguru import logger
from app.config import settings


class CrossEncoderReranker:
    """
    Second-stage ranker using Cross-Encoder architectures (e.g. BAAI/bge-reranker-large).
    Enforces deep token-level cross-attention between the query and candidate documents.
    """

    def __init__(self, model_name: str = settings.RERANKER_MODEL):
        self.model_name = model_name
        self._model = None

    def _get_model(self):
        """
        TODO [Bài tập 1]: Tải mô hình `CrossEncoder` theo cơ chế Lazy-loading & Fallback:
        1. Nếu `self._model is None`:
           Bọc trong khối try...except:
           - Import `from sentence_transformers import CrossEncoder`
           - Khởi tạo: `self._model = CrossEncoder(self.model_name)`
           - Nếu có Exception (ví dụ: máy dev không có mạng / chưa tải trọng số):
             Ghi log cảnh báo: `logger.warning(f"Failed to load CrossEncoder ({e}). Falling back to passthrough.")`
             Gán `self._model = False` (để không thử tải lại nhiều lần gây chậm).
        2. Trả về `self._model`.
        """
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder
                self._model = CrossEncoder(self.model_name)
            except Exception as e:
                logger.warning(f"Failed to load CrossEncoder ({e}). Falling back to passthrough.")
                self._model = False
                
        return self._model

    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_n: int = settings.TOP_K_RERANKED
    ) -> List[Dict[str, Any]]:
        """
        TODO [Bài tập 2]: Chấm lại điểm và lọc ra top_n tài liệu xuất sắc nhất:
        1. Nếu danh sách `documents` rỗng: `return []`.
        2. Lấy model qua `model = self._get_model()`.
        3. Nếu `not model` (chế độ fallback): trả về `documents[:top_n]`.
        4. Chuẩn bị danh sách các cặp câu hỏi - tài liệu:
           `sentence_pairs = [[query, doc["content"]] for doc in documents]`
        5. Gọi model dự đoán điểm:
           `scores = model.predict(sentence_pairs)`
        6. Duyệt qua từng cặp và gán điểm vào document:
           for idx, score in enumerate(scores):
               documents[idx]["rerank_score"] = float(score)
        7. Sắp xếp danh sách documents theo `rerank_score` giảm dần.
        8. Trả về `top_n` tài liệu đầu tiên.
        """
        if not documents:
            return []

        model = self._get_model()
        if not model:
            return documents[:top_n]

        sentence_pairs = [[query, doc["content"]] for doc in documents]
        scores = model.predict(sentence_pairs)

        for idx, score in enumerate(scores):
            documents[idx]["rerank_score"] = float(score)

        documents.sort(key=lambda x: x["rerank_score"], reverse=True)
        return documents[:top_n]
