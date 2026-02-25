from pydantic import BaseModel, Field
from typing import Optional, List

class SettingsBase(BaseModel):
    """设置基础模型"""
    save_folder: str = Field(..., description="保存文件夹")
    download_videos: bool = Field(True, description="下载视频")
    download_images: bool = Field(False, description="下载图集")
    name_format: List[str] = Field(default_factory=lambda: ["create_time", "id", "type", "desc"], description="文件名格式")
    split: str = Field("-", description="分隔符")
    date_format: str = Field("%Y-%m-%d", description="日期格式")
    proxy: Optional[str] = Field(None, description="代理设置")
    file_description_max_length: int = Field(64, description="文件描述最大长度")
    chunk_size: int = Field(1048576, description="下载块大小")
    timeout: int = Field(300, description="超时设置")
    concurrency: int = Field(5, description="并发数")

class SettingsUpdate(BaseModel):
    """更新设置模型"""
    save_folder: Optional[str] = Field(None, description="保存文件夹")
    download_videos: Optional[bool] = Field(None, description="下载视频")
    download_images: Optional[bool] = Field(None, description="下载图集")
    name_format: Optional[List[str]] = Field(None, description="文件名格式")
    split: Optional[str] = Field(None, description="分隔符")
    date_format: Optional[str] = Field(None, description="日期格式")
    proxy: Optional[str] = Field(None, description="代理设置")
    file_description_max_length: Optional[int] = Field(None, description="文件描述最大长度")
    chunk_size: Optional[int] = Field(None, description="下载块大小")
    timeout: Optional[int] = Field(None, description="超时设置")
    concurrency: Optional[int] = Field(None, description="并发数")

class SettingsResponse(SettingsBase):
    """设置响应模型"""
    id: int = Field(..., description="设置ID")
    
    class Config:
        from_attributes = True
