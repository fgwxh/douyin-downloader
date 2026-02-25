from typing import Dict
from app.schemas.cookie import CookieUpdate, CookieResponse
from app.core.config import settings
import json
import os
from pathlib import Path
from datetime import datetime
from cryptography.fernet import Fernet

class CookieService:
    """Cookie服务"""
    
    def __init__(self):
        """初始化Cookie服务"""
        self.cookie_file = Path("./data/cookies.json")
        self.key_file = Path("./data/encryption_key.key")
        self._ensure_key_file()
        self._ensure_cookie_file()
    
    def _ensure_cookie_file(self):
        """确保Cookie文件存在"""
        if not self.cookie_file.exists():
            # 创建默认Cookie
            default_cookie = {"cookies": {}}
            # 确保目录存在
            self.cookie_file.parent.mkdir(exist_ok=True)
            # 加密并保存默认Cookie
            encrypted_cookie = self._encrypt_data(default_cookie)
            with open(self.cookie_file, "wb") as f:
                f.write(encrypted_cookie)
    
    def _ensure_key_file(self):
        """确保密钥文件存在"""
        if not self.key_file.exists():
            # 生成并保存密钥
            key = Fernet.generate_key()
            # 确保目录存在
            self.key_file.parent.mkdir(exist_ok=True)
            # 保存密钥
            with open(self.key_file, "wb") as f:
                f.write(key)
            # 设置文件权限（仅在类Unix系统上有效）
            if os.name != "nt":  # 不是Windows系统
                try:
                    os.chmod(self.key_file, 0o600)
                except Exception:
                    pass
    
    def _load_key(self) -> bytes:
        """加载加密密钥"""
        with open(self.key_file, "rb") as f:
            return f.read()
    
    def _encrypt_data(self, data: dict) -> bytes:
        """加密数据"""
        key = self._load_key()
        cipher_suite = Fernet(key)
        data_json = json.dumps(data, ensure_ascii=False).encode()
        return cipher_suite.encrypt(data_json)
    
    def _decrypt_data(self, encrypted_data: bytes) -> dict:
        """解密数据"""
        try:
            key = self._load_key()
            cipher_suite = Fernet(key)
            decrypted_data = cipher_suite.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            # 解密失败，返回默认空Cookie
            print(f"解密数据失败: {e}")
            return {"cookies": {}}
    
    def _load_cookie(self) -> dict:
        """加载Cookie"""
        try:
            with open(self.cookie_file, "rb") as f:
                encrypted_data = f.read()
            return self._decrypt_data(encrypted_data)
        except Exception as e:
            # 加载失败，重新创建Cookie文件
            print(f"加载Cookie失败: {e}")
            default_cookie = {"cookies": {}}
            encrypted_cookie = self._encrypt_data(default_cookie)
            with open(self.cookie_file, "wb") as f:
                f.write(encrypted_cookie)
            return default_cookie
    
    def _save_cookie(self, cookie: dict):
        """保存Cookie"""
        encrypted_data = self._encrypt_data(cookie)
        with open(self.cookie_file, "wb") as f:
            f.write(encrypted_data)
    
    async def get_cookie(self) -> CookieResponse:
        """获取当前Cookie"""
        # 加载Cookie
        loaded_cookie = self._load_cookie()
        
        # 构建响应
        response = CookieResponse(
            id=1,  # 固定ID
            cookies=loaded_cookie.get("cookies", {}),
            updated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        return response
    
    async def update_cookie(self, cookie_update: CookieUpdate) -> CookieResponse:
        """更新Cookie"""
        # 加载Cookie
        loaded_cookie = self._load_cookie()
        
        # 更新Cookie
        loaded_cookie["cookies"] = cookie_update.cookies
        
        # 保存Cookie
        self._save_cookie(loaded_cookie)
        
        # 构建响应
        response = CookieResponse(
            id=1,  # 固定ID
            cookies=loaded_cookie.get("cookies", {}),
            updated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        return response
    
    async def delete_cookie(self):
        """删除Cookie"""
        # 创建空Cookie
        empty_cookie = {"cookies": {}}
        
        # 保存空Cookie
        self._save_cookie(empty_cookie)
