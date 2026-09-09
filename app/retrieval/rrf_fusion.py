"""
Enterprise Agentic Knowledge Platform (EAKP)
Module: app/retrieval/rrf_fusion.py
Purpose: Reciprocal Rank Fusion (RRF) Algorithm to blend Dense and Sparse Rankings.
"""

from typing import List, Dict, Any


class ReciprocalRankFusion:
    """
    Implements Reciprocal Rank Fusion (RRF).
    Standardizes and fuses disparate score scales from Vector Search and Keyword/BM25 Search.
    Formula: RRF_Score(d) = sum( 1 / (k + rank(d)) )
    """

    @staticmethod
    def fuse(
        dense_results: List[Dict[str, Any]],
        sparse_results: List[Dict[str, Any]],
        k: int = 60
    ) -> List[Dict[str, Any]]:
         """
         TODO [Bài tập 1]: Hòa trộn kết quả từ Dense Search và Sparse Search theo thuật toán RRF:
         1. Khởi tạo:
            - `doc_scores: Dict[str, float] = {}`: Lưu tổng điểm RRF của mỗi tài liệu.
            - `doc_map: Dict[str, Dict[str, Any]] = {}`: Lưu nội dung của tài liệu theo id.
         
         2. Duyệt qua `dense_results` bằng `enumerate(..., start=1)` để lấy `rank`:
            - Lấy `doc_id = str(item["id"])`
            - Lưu item vào `doc_map[doc_id] = item`
            - Cộng dồn điểm: `doc_scores[doc_id] = doc_scores.get(doc_id, 0.0) + (1.0 / (k + rank))`

         3. Duyệt qua `sparse_results` bằng `enumerate(..., start=1)` để lấy `rank`:
            - Lấy `doc_id = str(item["id"])`
            - Nếu `doc_id` chưa có trong `doc_map`, lưu `doc_map[doc_id] = item`
            - Cộng dồn điểm: `doc_scores[doc_id] = doc_scores.get(doc_id, 0.0) + (1.0 / (k + rank))`

         4. Sắp xếp các `doc_id` theo điểm RRF giảm dần:
            `sorted_ids = sorted(doc_scores.keys(), key=lambda x: doc_scores[x], reverse=True)`

         5. Duyệt qua `sorted_ids`:
            - Lấy bản sao của item từ `doc_map[doc_id]`
            - Gán thêm thuộc tính `"rrf_score": doc_scores[doc_id]`
            - Append vào danh sách `fused_results`

         6. Trả về `fused_results`.
         """
        
         doc_scores: Dict[str, float] = {}
         doc_map: Dict[str, Dict[str, Any]] = {}
         
         for rank, item in enumerate(dense_results, start=1):
            doc_id = str(item["id"])
            doc_map[doc_id] = item
            doc_scores[doc_id] = doc_scores.get(doc_id, 0.0) + (1.0 / (k + rank))
            
         for rank, item in enumerate(sparse_results, start=1):
            doc_id = str(item["id"])
            if doc_id not in doc_map:
               doc_map[doc_id] = item
            doc_scores[doc_id] = doc_scores.get(doc_id, 0.0) + (1.0 / (k + rank))
            
         sorted_ids = sorted(doc_scores.keys(), key=lambda x: doc_scores[x], reverse=True)
         
         fused_results = []
         for doc_id in sorted_ids:
            item = dict(doc_map[doc_id])
            item["rrf_score"] = doc_scores[doc_id]
            fused_results.append(item)
         
         return fused_results
