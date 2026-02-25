from fastapi import APIRouter, Depends, HTTPException, Query
from app.schemas.works import WorkResponse, WorkListResponse
from app.services.works import WorkService

router = APIRouter()

@router.get("/", response_model=WorkListResponse)
async def get_works(
    account_id: int = Query(..., description="账号ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页大小"),
    earliest: str = Query(None, description="开始日期 (YYYY-MM-DD)"),
    latest: str = Query(None, description="结束日期 (YYYY-MM-DD)"),
    service: WorkService = Depends()
):
    """获取作品列表"""
    return await service.get_works(account_id, page, page_size, earliest, latest)

@router.get("/{work_id}", response_model=WorkResponse)
async def get_work(work_id: str, service: WorkService = Depends()):
    """获取单个作品"""
    work = await service.get_work(work_id)
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")
    return work

@router.post("/download")
async def download_selected_works(
    work_ids: list[str] = Query(..., description="作品ID列表"),
    service: WorkService = Depends()
):
    """下载选中的作品"""
    return await service.download_selected_works(work_ids)
