from fastapi import APIRouter, Depends
from app.schemas.cookie import CookieUpdate, CookieResponse
from app.services.cookie import CookieService

router = APIRouter()

@router.get("/", response_model=CookieResponse)
async def get_cookie(service: CookieService = Depends()):
    """获取当前Cookie"""
    return await service.get_cookie()

@router.put("/", response_model=CookieResponse)
async def update_cookie(cookie: CookieUpdate, service: CookieService = Depends()):
    """更新Cookie"""
    return await service.update_cookie(cookie)

@router.delete("/")
async def delete_cookie(service: CookieService = Depends()):
    """删除Cookie"""
    await service.delete_cookie()
    return {"message": "Cookie已删除"}
