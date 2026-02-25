from typing import Dict, Any
import json
import base64
from pathlib import Path
from cryptography.fernet import Fernet
from app.core.config import settings

class ConfigService:
    """配置管理服务"""
    
    def __init__(self):
        """初始化配置管理服务"""
        self.config_file = Path("./data/settings_mine.json")
        self.cookie_file = Path("./data/cookies.json")
        self.key_file = Path("./data/encryption_key.key")
        self.default_config = {
            "accounts": [],
            "save_folder": ".",
            "download_videos": True,
            "download_images": False,
            "proxy": "",
            "timeout": 300,
            "concurrency": 5
        }
    
    def _load_key(self):
        """加载加密密钥"""
        if not self.key_file.exists():
            # 生成新密钥
            key = Fernet.generate_key()
            # 确保目录存在
            self.key_file.parent.mkdir(exist_ok=True)
            # 保存密钥
            with open(self.key_file, "wb") as f:
                f.write(key)
            return key
        with open(self.key_file, "rb") as f:
            return f.read()
    
    def _load_cookie(self) -> Dict[str, Any]:
        """加载Cookie"""
        if not self.cookie_file.exists():
            return {"cookies": {}}
        try:
            # 尝试以二进制模式读取并解密Cookie
            key = self._load_key()
            cipher_suite = Fernet(key)
            
            # 读取加密的Cookie
            with open(self.cookie_file, "rb") as f:
                encrypted_data = f.read()
            
            # 解密Cookie
            if encrypted_data:
                decrypted_data = cipher_suite.decrypt(encrypted_data)
                return json.loads(decrypted_data.decode())
        except Exception:
            # 解密失败，返回默认Cookie
            pass
        return {"cookies": {}}
    
    def _save_cookie(self, cookie_data: Dict[str, Any]):
        """保存Cookie"""
        # 确保目录存在
        self.cookie_file.parent.mkdir(exist_ok=True)
        
        # 加密Cookie数据
        key = self._load_key()
        cipher_suite = Fernet(key)
        cookie_json = json.dumps(cookie_data, ensure_ascii=False).encode()
        encrypted_data = cipher_suite.encrypt(cookie_json)
        
        # 保存加密后的Cookie
        with open(self.cookie_file, "wb") as f:
            f.write(encrypted_data)
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        if not self.config_file.exists():
            return self.default_config
        
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return self.default_config
    
    def _save_config(self, config: Dict[str, Any]):
        """保存配置"""
        # 确保目录存在
        self.config_file.parent.mkdir(exist_ok=True)
        
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    
    async def get_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        # 加载基本配置
        config = self._load_config()
        
        # 不添加加密的Cookie信息到配置中
        # 原因：加密Cookie是与特定环境的密钥绑定的，在不同环境之间导出导入会导致解密失败
        
        return config
    
    async def import_config(self, config: Dict[str, Any]):
        """导入配置"""
        # 从配置中移除Cookie信息，不导入加密的Cookie数据
        # 原因：加密Cookie是与特定环境的密钥绑定的，在不同环境之间导入会导致解密失败
        config_without_cookie = config.copy()
        if "cookies" in config_without_cookie:
            del config_without_cookie["cookies"]
        # 保存配置
        self._save_config(config_without_cookie)
    
    async def init_config(self):
        """初始化配置"""
        # 保存默认配置
        self._save_config(self.default_config)
        
        # 清空Cookie
        try:
            if self.cookie_file.exists():
                self.cookie_file.unlink()
        except Exception:
            # 处理异常，确保初始化配置不失败
            pass
        
        # 清空密钥文件（在Docker环境中，这将强制生成新密钥）
        try:
            if self.key_file.exists():
                self.key_file.unlink()
        except Exception:
            # 处理异常，确保初始化配置不失败
            pass
