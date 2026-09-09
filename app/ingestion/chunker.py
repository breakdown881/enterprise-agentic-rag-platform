"""
Enterprise Agentic Knowledge Platform (EAKP)
Module: app/ingestion/chunker.py
Purpose: Context-Aware Recursive & Hierarchical Chunking with Rich Metadata.
"""

from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import settings


class SmartChunker:
    """
    Context-aware chunker that respects document headers, paragraph boundaries,
    and attaches comprehensive metadata for downstream Hybrid Search and Citations.
    """

    def __init__(
        self,
        chunk_size: int = settings.CHUNK_SIZE,
        chunk_overlap: int = settings.CHUNK_OVERLAP
    ):
        """
        TODO [Bài tập 1]: Khởi tạo `self.splitter` bằng `RecursiveCharacterTextSplitter`:
        - chunk_size: Truyền vào `chunk_size`
        - chunk_overlap: Truyền vào `chunk_overlap`
        - separators: Danh sách ưu tiên cắt theo thứ tự từ lớn đến nhỏ:
          ["\n## ", "\n### ", "\n\n", "\n", ". ", " ", ""]
        - length_function: len (hoặc hàm đếm token)
        """
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " ", ""],
            length_function=len
        )

    def split_document(
        self,
        parsed_pages: List[Dict[str, Any]],
        doc_id: str
    ) -> List[Dict[str, Any]]:
        """
        TODO [Bài tập 2]: Duyệt qua danh sách trang đã bóc tách và tạo chunks có metadata:
        1. Khởi tạo danh sách kết quả: `chunks = []`.
        2. Duyệt qua từng `page_data` trong `parsed_pages`.
        3. Lấy `page_text = page_data.get("text", "")`. Nếu text rỗng thì bỏ qua (continue).
        4. Dùng `self.splitter.split_text(page_text)` để chia nhỏ thành danh sách các chuỗi text.
        5. Lặp qua từng đoạn `chunk_text` (dùng enumerate với `idx` bắt đầu từ 0):
           Tạo một dict đại diện cho chunk:
           {
               "doc_id": doc_id,
               "chunk_index": idx,
               "content": chunk_text,
               "metadata": {
                   "source": page_data.get("source"),
                   "page_number": page_data.get("page_number"),
                   "has_tables": page_data.get("tables_count", 0) > 0,
                   "char_length": len(chunk_text)
               }
           }
           và append vào `chunks`.
        6. Trả về danh sách `chunks`.
        """
        chunks = []
        for page_data in parsed_pages:
            page_text = page_data.get("text", "")
            if not page_text:
                continue
            
            chunk_texts = self.splitter.split_text(page_text)
            for idx, chunk_text in enumerate(chunk_texts):
                chunk = {
                    "doc_id": doc_id,
                    "chunk_index": idx,
                    "content": chunk_text,
                    "metadata": {
                        "source": page_data.get("source"),
                        "page_number": page_data.get("page_number"),
                        "has_tables": page_data.get("tables_count", 0) > 0,
                        "char_length": len(chunk_text)
                    }
                }
                chunks.append(chunk)
                
        return chunks
