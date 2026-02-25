from pydantic import BaseModel, Field, validator
from typing import Dict, Optional, Union

class CookieBase(BaseModel):
    """Cookie基础模型"""
    cookies: Union[Dict[str, str], str] = Field(..., description="Cookie字典或字符串")

class CookieUpdate(BaseModel):
    """更新Cookie模型"""
    cookies: Union[Dict[str, str], str] = Field(..., description="Cookie字典或字符串")
    
    @validator('cookies', pre=True)
    def validate_cookies(cls, v):
        """验证并解析Cookie"""
        if isinstance(v, dict):
            return v
        elif isinstance(v, str):
            # 解析字符串格式的Cookie
            cookies_dict = {}
            # 按分号分割Cookie键值对
            cookie_pairs = v.split(';')
            for pair in cookie_pairs:
                pair = pair.strip()
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    cookies_dict[key.strip()] = value.strip()
            return cookies_dict
        else:
            raise ValueError('Cookie必须是字典或字符串格式')

class CookieResponse(BaseModel):
    """Cookie响应模型"""
    id: int = Field(..., description="Cookie ID")
    cookies: Dict[str, str] = Field(..., description="Cookie字典")
    updated_at: str = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True
