from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """应用配置"""
    # 应用设置
    APP_NAME: str = "抖音作品下载工具"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # 数据库设置
    DATABASE_URL: str = "sqlite:///./douyin_download.db"
    
    # CORS设置 - 允许所有来源，适应不同部署环境
    CORS_ORIGINS: List[str] = ["*"]
    
    # 文件设置
    UPLOAD_DIR: str = "./downloads"
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    
    # 下载设置
    DOWNLOAD_TIMEOUT: int = 300
    DOWNLOAD_CHUNK_SIZE: int = 1048576  # 1MB
    DOWNLOAD_CONCURRENCY: int = 5
    
    # API设置
    API_V1_STR: str = "/api"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# 创建全局设置对象
settings = Settings()
