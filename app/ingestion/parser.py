"""
Enterprise Agentic Knowledge Platform (EAKP)
Module: app/ingestion/parser.py
Purpose: Enterprise Document Parser for PDF and Markdown files with Table Preservation.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import pdfplumber
from loguru import logger


class DocumentParser:
    """
    Parser for enterprise unstructured files.
    Preserves table structures (converts to Markdown table syntax) and attaches page metadata.
    """

    @classmethod
    def _format_table_as_markdown(cls, table: List[List[Optional[str]]]) -> str:
        """
        Helper: Chuyển đổi ma trận table 2 chiều thành định dạng Markdown Table.
        Ví dụ:
        | Cột 1 | Cột 2 |
        | --- | --- |
        | Dòng 1A | Dòng 1B |
        """
        if not table or len(table) < 1:
            return ""

        # Lọc các ô None thành chuỗi rỗng và làm sạch khoảng trắng
        cleaned_table = [
            [str(cell).strip() if cell is not None else "" for cell in row]
            for row in table
        ]

        # Header
        header = cleaned_table[0]
        md_lines = ["| " + " | ".join(header) + " |"]
        md_lines.append("| " + " | ".join(["---"] * len(header)) + " |")

        # Data rows
        for row in cleaned_table[1:]:
            # Đảm bảo số cột khớp với header
            padded_row = row + [""] * (len(header) - len(row))
            md_lines.append("| " + " | ".join(padded_row[:len(header)]) + " |")

        return "\n".join(md_lines)

    @classmethod
    def parse_pdf(cls, file_path: Path) -> List[Dict[str, Any]]:
        """
        TODO [Bài tập 1]: Bóc tách file PDF bằng `pdfplumber`:
        1. Khởi tạo danh sách kết quả `pages_data = []`.
        2. Dùng context manager mở file: `with pdfplumber.open(file_path) as pdf:`
        3. Lặp qua từng trang `page` trong `pdf.pages` với `page_number` bắt đầu từ 1.
        4. Trích xuất text: `text = page.extract_text() or ""`
        5. Trích xuất bảng: `tables = page.extract_tables() or []`
        6. Duyệt qua từng `tbl` trong `tables`, gọi `cls._format_table_as_markdown(tbl)` 
           và nối vào chuỗi `text` để LLM hiểu được cấu trúc bảng biểu.
        7. Thêm dict vào `pages_data`:
           {
               "page_number": page_number,
               "text": text,
               "source": file_path.name,
               "tables_count": len(tables)
           }
        8. Xử lý try/except bắt lỗi và log bằng `logger.error(...)`.
        9. Trả về `pages_data`.
        """
        pages_data = []
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_number, page in enumerate(pdf.pages, start=1):
                    try:
                        text = page.extract_text() or ""
                        tables = page.extract_tables() or []
                        
                        # Chuyển đổi các bảng sang định dạng Markdown và nối vào text
                        for tbl in tables:
                            md_table = cls._format_table_as_markdown(tbl)
                            text += "\n\n" + md_table  # Nối bảng vào cuối text
                            
                    except Exception as e:
                        logger.error(f"Error extracting page {page_number} from {file_path.name}: {e}")
                        text = ""
                        tables = []
                        
                    pages_data.append({
                        "page_number": page_number,
                        "text": text,
                        "source": file_path.name,
                        "tables_count": len(tables)
                    })
        except Exception as e:
            logger.error(f"Error opening PDF file {file_path.name}: {e}")
        return pages_data

    @classmethod
    def parse_markdown(cls, file_path: Path) -> List[Dict[str, Any]]:
        """
        TODO [Bài tập 2]: Bóc tách file Markdown / Text (.md, .txt):
        1. Đọc nội dung file dạng text UTF-8: `content = file_path.read_text(encoding="utf-8")`
        2. Trả về list gồm 1 dict:
           [{
               "page_number": 1,
               "text": content,
               "source": file_path.name,
               "tables_count": 0
           }]
        3. Bọc trong try/except để phòng trường hợp file không tồn tại hoặc lỗi encode.
        """
        try:
            content = file_path.read_text(encoding="utf-8")
            return [{
                "page_number": 1,
                "text": content,
                "source": file_path.name,
                "tables_count": 0
            }]
        except Exception as e:
            logger.error(f"Error reading markdown file {file_path.name}: {e}")
            return []
        
