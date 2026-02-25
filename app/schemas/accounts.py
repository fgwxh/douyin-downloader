from pydantic import BaseModel, Field
from typing import Optional

class AccountBase(BaseModel):
    """账号基础模型"""
    mark: str = Field(..., description="账号标识")
    url: str = Field(..., description="账号主页链接")
    earliest: str = Field(..., description="最早发布日期")
    latest: str = Field(..., description="最晚发布日期")

class AccountCreate(AccountBase):
    """创建账号模型"""
    pass

class AccountUpdate(BaseModel):
    """更新账号模型"""
    mark: Optional[str] = Field(None, description="账号标识")
    url: Optional[str] = Field(None, description="账号主页链接")
    earliest: Optional[str] = Field(None, description="最早发布日期")
    latest: Optional[str] = Field(None, description="最晚发布日期")

class AccountResponse(AccountBase):
    """账号响应模型"""
    id: int = Field(..., description="账号ID")
    
    class Config:
        from_attributes = True
