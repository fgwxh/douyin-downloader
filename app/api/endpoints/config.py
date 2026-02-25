from fastapi import APIRouter, Depends
from typing import Dict, Any
from app.services.config import ConfigService

router = APIRouter()

@router.get("/", response_model=Dict[str, Any])
async def get_config(service: ConfigService = Depends()):
    """获取当前配置"""
    return await service.get_config()

@router.post("/import")
async def import_config(config: Dict[str, Any], service: ConfigService = Depends()):
    """导入配置"""
    await service.import_config(config)
    return {"message": "配置导入成功"}

@router.post("/init")
async def init_config(service: ConfigService = Depends()):
    """初始化配置"""
    await service.init_config()
    return {"message": "配置初始化成功"}
