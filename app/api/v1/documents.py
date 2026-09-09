"""
Enterprise Agentic Knowledge Platform (EAKP)
Module: app/api/v1/documents.py
Purpose: Document Upload & Asynchronous Background Ingestion Pipeline.
"""

import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from pydantic import BaseModel
from loguru import logger

from app.core.database import AsyncSessionLocal
from app.ingestion.parser import DocumentParser
from app.ingestion.chunker import SmartChunker
from app.ingestion.vector_store import PostgresVectorStore


router = APIRouter(prefix="/documents", tags=["Documents & Ingestion"])

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


async def process_document_background(file_path: Path, doc_id: str, filename: str):
    """
    Tác vụ nền (Background Task):
    Bóc tách file -> Chia chunk -> Embed và lưu vào PostgreSQL pgvector.
    Không làm nghẽn HTTP request của người dùng!
    """
    try:
        logger.info(f"Starting background ingestion for: {filename} (id={doc_id})")
        
        # 1. Parse file theo định dạng
        if file_path.suffix.lower() == ".pdf":
            pages = DocumentParser.parse_pdf(file_path)
        else:
            pages = DocumentParser.parse_markdown(file_path)

        if not pages:
            logger.warning(f"No text extracted from {filename}")
            return

        # 2. Chunking thông minh
        chunker = SmartChunker()
        chunks = chunker.split_document(pages, doc_id=doc_id)

        # 3. Upsert vào pgvector
        async with AsyncSessionLocal() as session:
            vector_store = PostgresVectorStore(session)
            count = await vector_store.upsert_chunks(chunks, doc_title=filename)
            logger.info(f"Completed ingestion for {filename}: {count} chunks indexed.")

    except Exception as e:
        logger.error(f"Background ingestion failed for {filename}: {e}")


@router.post("/ingest")
async def ingest_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    TODO [Bài tập 1]: Triển khai API Ingest tài liệu:
    1. Kiểm tra định dạng file (chỉ cho phép .pdf, .md, .txt):
       ext = Path(file.filename).suffix.lower()
       if ext not in [".pdf", ".md", ".txt"]:
           raise HTTPException(status_code=400, detail="Chỉ hỗ trợ file .pdf, .md, .txt")

    2. Lưu file vào thư mục UPLOAD_DIR:
       save_path = UPLOAD_DIR / file.filename
       with save_path.open("wb") as buffer:
           shutil.copyfileobj(file.file, buffer)

    3. Tạo doc_id ngẫu nhiên:
       import uuid; doc_id = str(uuid.uuid4())

    4. Đẩy tác vụ bóc tách vào Background Tasks:
       background_tasks.add_task(process_document_background, save_path, doc_id, file.filename)

    5. Trả về response JSON ngay lập tức:
       return {
           "status": "processing",
           "message": f"File '{file.filename}' đã được tiếp nhận và đang xử lý nền.",
           "doc_id": doc_id
       }
    """
    ext = Path(file.filename).suffix.lower()
    if ext not in [".pdf", ".md", ".txt"]:
        raise HTTPException(status_code=400, detail="Chỉ hỗ trợ file .pdf, .md, .txt")
    
    save_path = UPLOAD_DIR / file.filename
    with save_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    import uuid
    doc_id = str(uuid.uuid4())
    background_tasks.add_task(process_document_background, save_path, doc_id, file.filename)
    
    return {
        "status": "processing",
        "message": f"File '{file.filename}' đã được tiếp nhận và đang xử lý nền.",
        "doc_id": doc_id
    }
