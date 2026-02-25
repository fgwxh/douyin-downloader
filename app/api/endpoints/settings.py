from fastapi import APIRouter, Depends
from app.schemas.settings import SettingsUpdate, SettingsResponse
from app.services.settings import SettingsService

router = APIRouter()

@router.get("/", response_model=SettingsResponse)
async def get_settings(service: SettingsService = Depends()):
    """获取当前设置"""
    return await service.get_settings()

@router.put("/", response_model=SettingsResponse)
async def update_settings(settings: SettingsUpdate, service: SettingsService = Depends()):
    """更新设置"""
    return await service.update_settings(settings)
