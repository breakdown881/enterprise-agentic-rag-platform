"""
Enterprise Agentic Knowledge Platform (EAKP)
Module: app/api/v1/analytics.py
Purpose: System Healthcheck and Diagnostic Metrics for Docker / K8s probes.
"""

from fastapi import APIRouter
from sqlalchemy import text
from app.core.database import AsyncSessionLocal
from app.core.redis_cache import cache_manager


router = APIRouter(prefix="/analytics", tags=["Analytics & Health"])


@router.get("/health")
async def health_check():
    """
    TODO [Bài tập 2]: Triển khai Healthcheck endpoint kiểm tra Liveness của Postgres và Redis:
    1. Kiểm tra PostgreSQL:
       postgres_status = "healthy"
       try:
           async with AsyncSessionLocal() as session:
               await session.execute(text("SELECT 1"))
       except Exception as e:
           postgres_status = f"unhealthy: {str(e)}"

    2. Kiểm tra Redis:
       redis_status = "healthy" if cache_manager.client else "disconnected / bypass"

    3. Trả về:
       return {
           "status": "online" if postgres_status == "healthy" else "degraded",
           "database": postgres_status,
           "redis_cache": redis_status,
           "version": "1.0.0"
       }
    """
    postgres_status = "healthy"
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception as e:
        postgres_status = f"unhealthy: {str(e)}"
        
    redis_status = "healthy" if cache_manager.client else "disconnected / bypass"
    
    return {
        "status": "online" if postgres_status == "healthy" else "degraded",
        "database": postgres_status,
        "redis_cache": redis_status,
        "version": "1.0.0"
    }
