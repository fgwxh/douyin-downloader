from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class WorkBase(BaseModel):
    """作品基础模型"""
    id: str = Field(..., description="作品ID")
    desc: str = Field(..., description="作品描述")
    create_time: datetime = Field(..., description="创建时间")
    type: str = Field(..., description="作品类型")
    width: int = Field(..., description="宽度")
    height: int = Field(..., description="高度")
    downloads: List[str] = Field(..., description="下载链接")
    cover_url: Optional[str] = Field(None, description="封面图URL")

class WorkResponse(WorkBase):
    """作品响应模型"""
    account_id: int = Field(..., description="账号ID")
    account_mark: str = Field(..., description="账号标识")
    
    class Config:
        from_attributes = True

class WorkListResponse(BaseModel):
    """作品列表响应模型"""
    items: List[WorkResponse] = Field(..., description="作品列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    has_more: bool = Field(..., description="是否有更多")
