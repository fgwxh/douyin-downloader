from fastapi import APIRouter, Depends, HTTPException
from app.schemas.accounts import AccountCreate, AccountUpdate, AccountResponse
from app.services.accounts import AccountService

router = APIRouter()

@router.post("/", response_model=AccountResponse)
async def create_account(account: AccountCreate, service: AccountService = Depends()):
    """创建新账号"""
    return await service.create_account(account)

@router.get("/", response_model=list[AccountResponse])
async def get_accounts(service: AccountService = Depends()):
    """获取所有账号"""
    return await service.get_accounts()

@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(account_id: int, service: AccountService = Depends()):
    """获取单个账号"""
    account = await service.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")
    return account

@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(account_id: int, account: AccountUpdate, service: AccountService = Depends()):
    """更新账号"""
    updated_account = await service.update_account(account_id, account)
    if not updated_account:
        raise HTTPException(status_code=404, detail="账号不存在")
    return updated_account

@router.delete("/{account_id}")
async def delete_account(account_id: int, service: AccountService = Depends()):
    """删除账号"""
    deleted = await service.delete_account(account_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="账号不存在")
    return {"message": "账号删除成功"}
