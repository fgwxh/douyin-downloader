from typing import List, Optional
from app.schemas.accounts import AccountCreate, AccountUpdate, AccountResponse
from app.core.config import settings
import json
from pathlib import Path

class AccountService:
    """账号服务"""
    
    def __init__(self):
        """初始化账号服务"""
        self.settings_file = Path("./data/settings_mine.json")
        self._ensure_settings_file()
    
    def _ensure_settings_file(self):
        """确保设置文件存在"""
        if not self.settings_file.exists():
            # 创建默认设置
            default_settings = {
                "accounts": [],
                "save_folder": ".",
                "download_videos": True,
                "download_images": False,
                "name_format": ["create_time", "id", "type", "desc"],
                "split": "-",
                "date_format": "%Y-%m-%d",
                "proxy": "",
                "file_description_max_length": 64,
                "chunk_size": 1048576,
                "timeout": 300,
                "concurrency": 5
            }
            # 确保目录存在
            self.settings_file.parent.mkdir(exist_ok=True)
            # 写入默认设置
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(default_settings, f, ensure_ascii=False, indent=4)
    
    def _load_settings(self) -> dict:
        """加载设置"""
        with open(self.settings_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def _save_settings(self, settings: dict):
        """保存设置"""
        with open(self.settings_file, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)
    
    async def create_account(self, account: AccountCreate) -> AccountResponse:
        """创建新账号"""
        # 加载设置
        settings = self._load_settings()
        
        # 生成账号ID
        account_id = len(settings["accounts"]) + 1
        
        # 创建账号字典
        account_dict = {
            "id": account_id,
            "mark": account.mark,
            "url": account.url,
            "earliest": account.earliest,
            "latest": account.latest
        }
        
        # 添加到账号列表
        settings["accounts"].append(account_dict)
        
        # 保存设置
        self._save_settings(settings)
        
        # 返回响应
        return AccountResponse(**account_dict)
    
    async def get_accounts(self) -> List[AccountResponse]:
        """获取所有账号"""
        # 加载设置
        settings = self._load_settings()
        
        # 转换为响应模型，为每个账号添加id字段
        accounts = []
        for i, account in enumerate(settings["accounts"]):
            # 为账号添加id字段（索引+1）
            account_with_id = account.copy()
            account_with_id["id"] = i + 1
            accounts.append(AccountResponse(**account_with_id))
        
        return accounts
    
    async def get_account(self, account_id: int) -> Optional[AccountResponse]:
        """获取单个账号"""
        # 加载设置
        settings = self._load_settings()
        
        # 查找账号
        for i, account in enumerate(settings["accounts"]):
            # 使用索引+1作为账号ID
            if i + 1 == account_id:
                # 为账号添加id字段
                account_with_id = account.copy()
                account_with_id["id"] = i + 1
                return AccountResponse(**account_with_id)
        
        return None
    
    async def update_account(self, account_id: int, account: AccountUpdate) -> Optional[AccountResponse]:
        """更新账号"""
        # 加载设置
        settings = self._load_settings()
        
        # 查找并更新账号
        for i, acc in enumerate(settings["accounts"]):
            # 使用索引+1作为账号ID
            if i + 1 == account_id:
                # 更新账号信息
                if account.mark is not None:
                    acc["mark"] = account.mark
                if account.url is not None:
                    acc["url"] = account.url
                if account.earliest is not None:
                    acc["earliest"] = account.earliest
                if account.latest is not None:
                    acc["latest"] = account.latest
                
                # 保存设置
                self._save_settings(settings)
                
                # 为账号添加id字段
                acc_with_id = acc.copy()
                acc_with_id["id"] = i + 1
                
                # 返回响应
                return AccountResponse(**acc_with_id)
        
        return None
    
    async def delete_account(self, account_id: int) -> bool:
        """删除账号"""
        # 加载设置
        settings = self._load_settings()
        
        # 查找并删除账号
        for i, acc in enumerate(settings["accounts"]):
            # 使用索引+1作为账号ID
            if i + 1 == account_id:
                settings["accounts"].pop(i)
                
                # 保存设置
                self._save_settings(settings)
                
                return True
        
        return False
