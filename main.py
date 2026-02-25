from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api import router
from app.core.config import settings
import os

# 创建FastAPI应用
app = FastAPI(
    title="抖音作品下载工具API",
    description="抖音作品下载工具的后端API接口",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置静态文件服务
frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
app.mount("/frontend", StaticFiles(directory=frontend_dir, html=True), name="frontend")

# 包含API路由
app.include_router(router, prefix="/api")

# 根路径 - 重定向到前端页面
from fastapi.responses import RedirectResponse

@app.get("/")
async def root():
    return RedirectResponse(url="/frontend")

# 健康检查
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
