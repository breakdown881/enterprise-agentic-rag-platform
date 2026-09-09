"""
Enterprise Agentic Knowledge Platform (EAKP)
Module: app/core/database.py
Purpose: Asynchronous SQLAlchemy Engine, Session Management, and Connection Pooling.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from app.config import settings


# =============================================================================
# 1. ASYNC ENGINE & CONNECTION POOLING
# =============================================================================
# TODO [Bài tập 1]: Khởi tạo `async_engine` sử dụng `create_async_engine`:
# - url: Lấy từ `settings.DATABASE_URL`
# - echo: Bật logging SQL nếu `settings.ENVIRONMENT == "development"`
# - pool_size: Kích thước connection pool cơ sở (khuyến nghị: 10)
# - max_overflow: Số connection tối đa được mở thêm khi traffic spike (khuyến nghị: 20)
# - pool_pre_ping: True (Kiểm tra liveness của connection trước khi dùng, tránh stale connection)

async_engine = create_async_engine(settings.DATABASE_URL, echo=(settings.ENVIRONMENT == "development"), pool_size=10, max_overflow=20, pool_pre_ping=True)


# =============================================================================
# 2. ASYNC SESSION FACTORY
# =============================================================================
# TODO [Bài tập 2]: Khởi tạo `AsyncSessionLocal` sử dụng `async_sessionmaker`:
# - bind: Kết nối tới `async_engine`
# - class_: Sử dụng `AsyncSession`
# - expire_on_commit: False (CỰC KỲ QUAN TRỌNG trong Async SQLAlchemy để tránh lỗi MissingGreenlet khi truy cập thuộc tính sau commit)
# - autoflush: False

AsyncSessionLocal = async_sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)


# Declarative Base cho các ORM Models sau này
Base = declarative_base()


# =============================================================================
# 3. FASTAPI DEPENDENCY INJECTION
# =============================================================================
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    TODO [Bài tập 3]: Viết hàm generator bất đồng bộ `get_db()` dùng làm Dependency cho FastAPI.
    - Mở session với cú pháp `async with AsyncSessionLocal() as session:`
    - yield session ra ngoài cho API route xử lý
    - Nếu có Exception xảy ra: rollback session (`await session.rollback()`) và quăng lại ngoại lệ (raise)
    - Trong khối finally: đảm bảo đóng session (`await session.close()`)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()
