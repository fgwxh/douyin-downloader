from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class DownloadStatus(str, Enum):
    """下载状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class DownloadRequest(BaseModel):
    """下载请求模型"""
    account_id: int = Field(..., description="账号ID")
    work_ids: List[str] = Field(..., description="作品ID列表")
    works: Optional[List[dict]] = Field(None, description="作品信息列表")

class DownloadResponse(BaseModel):
    """下载响应模型"""
    task_id: str = Field(..., description="下载任务ID")
    status: DownloadStatus = Field(..., description="下载状态")
    message: Optional[str] = Field(None, description="状态消息")
    progress: float = Field(0.0, description="下载进度")
    completed_count: int = Field(0, description="已完成数量")
    total_count: int = Field(0, description="总数量")

class DownloadStatusResponse(BaseModel):
    """下载状态响应模型"""
    task_id: str = Field(..., description="下载任务ID")
    status: DownloadStatus = Field(..., description="下载状态")
    message: Optional[str] = Field(None, description="状态消息")
    progress: float = Field(0.0, description="下载进度")
    completed_count: int = Field(0, description="已完成数量")
    total_count: int = Field(0, description="总数量")
