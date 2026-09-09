"""
Enterprise Agentic Knowledge Platform (EAKP)
Module: app/main.py
Purpose: FastAPI Application Entrypoint, Lifespan Event Management, CORS & Route Assembly.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings
from app.core.redis_cache import cache_manager
from app.api.v1.chat import router as chat_router
from app.api.v1.documents import router as documents_router
from app.api.v1.analytics import router as analytics_router


# =============================================================================
# 1. APPLICATION LIFESPAN (STARTUP & SHUTDOWN HOOKS)
# =============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    TODO [Bài tập 1]: Quản lý vòng đời ứng dụng FastAPI:
    - Khi khởi động (Startup):
      + Log: `logger.info("Initializing Enterprise Agentic Knowledge Platform...")`
      + Kết nối Redis Cache: `await cache_manager.connect()`
    - Dùng `yield` để ứng dụng nhận traffic.
    - Khi tắt server (Shutdown):
      + Log: `logger.info("Shutting down application...")`
      + Đóng kết nối Redis: `await cache_manager.close()`
    """
    logger.info("Initializing Enterprise Agentic Knowledge Platform...")
    await cache_manager.connect()
    yield
    logger.info("Shutting down application...")
    await cache_manager.close()


# =============================================================================
# 2. FASTAPI APP INITIALIZATION
# =============================================================================
app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Enterprise Multi-Agent Knowledge & Analytics Copilot (EAKP)",
    lifespan=lifespan
)


# =============================================================================
# 3. CORS MIDDLEWARE
# =============================================================================
# TODO [Bài tập 2]: Cấu hình CORSMiddleware cho app:
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# 4. ROUTER ASSEMBLY
# =============================================================================
# TODO [Bài tập 3]: Gom các sub-router v1 vào API chính:
# 1. Tạo router v1: `api_v1_router = APIRouter(prefix=settings.API_V1_STR)`
# 2. Include các router con:
#    api_v1_router.include_router(chat_router)
#    api_v1_router.include_router(documents_router)
#    api_v1_router.include_router(analytics_router)
# 3. Mount router v1 vào app:
#    app.include_router(api_v1_router)
api_v1_router = APIRouter(prefix=settings.API_V1_STR)
api_v1_router.include_router(chat_router)
api_v1_router.include_router(documents_router)
api_v1_router.include_router(analytics_router)
app.include_router(api_v1_router)


# =============================================================================
# 5. ROOT WELCOME ENDPOINT
# =============================================================================
@app.get("/", tags=["Root"])
async def root():
    return {
        "app_name": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "docs_url": "/docs",
        "health_url": f"{settings.API_V1_STR}/analytics/health"
    }
