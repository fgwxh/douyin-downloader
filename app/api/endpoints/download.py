from fastapi import APIRouter, Depends, HTTPException
from app.schemas.download import DownloadRequest, DownloadResponse
from app.services.download import DownloadService

router = APIRouter()

@router.post("/", response_model=DownloadResponse)
async def start_download(download_request: DownloadRequest, service: DownloadService = Depends()):
    """开始下载任务"""
    return await service.start_download(download_request)

@router.get("/status/{task_id}", response_model=DownloadResponse)
async def get_download_status(task_id: str, service: DownloadService = Depends()):
    """获取下载任务状态"""
    status = await service.get_download_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="下载任务不存在")
    return status

@router.post("/stop/{task_id}")
async def stop_download(task_id: str, service: DownloadService = Depends()):
    """停止下载任务"""
    stopped = await service.stop_download(task_id)
    if not stopped:
        raise HTTPException(status_code=404, detail="下载任务不存在")
    return {"message": "下载任务已停止"}
