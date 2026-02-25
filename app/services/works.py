from typing import List, Optional
from app.schemas.works import WorkResponse, WorkListResponse
from app.core.config import settings
import json
from pathlib import Path
from datetime import datetime
from src.download.acquire import Acquire
from src.download.parse import Parse
from src.config import Settings, Cookie
from src.tool.cleaner import Cleaner
import logging

class WorkService:
    """作品服务"""
    
    def __init__(self):
        """初始化作品服务"""
        self.settings_file = Path("./data/settings_mine.json")
        self.cookie_file = Path("./data/cookies.json")
        self._ensure_files()
    
    def _ensure_files(self):
        """确保文件存在"""
        # 确保设置文件存在
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
        
        # 确保Cookie文件存在
        if not self.cookie_file.exists():
            # 创建默认Cookie
            default_cookie = {"cookies": {}}
            # 写入默认Cookie
            with open(self.cookie_file, "w", encoding="utf-8") as f:
                json.dump(default_cookie, f, ensure_ascii=False, indent=4)
    
    def _load_settings(self) -> dict:
        """加载设置"""
        try:
            with open(self.settings_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            # 如果设置文件损坏或不存在，返回默认设置
            return {
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
    
    def _load_cookie(self) -> dict:
        """加载Cookie"""
        try:
            # 尝试以二进制模式读取并解密Cookie
            from cryptography.fernet import Fernet
            key_file = Path("./data/encryption_key.key")
            
            # 加载密钥
            if key_file.exists():
                with open(key_file, "rb") as f:
                    key = f.read()
                
                # 读取加密的Cookie
                with open(self.cookie_file, "rb") as f:
                    encrypted_data = f.read()
                
                # 解密Cookie
                if encrypted_data:
                    cipher_suite = Fernet(key)
                    decrypted_data = cipher_suite.decrypt(encrypted_data)
                    return json.loads(decrypted_data.decode())
        except Exception as e:
            # 解密失败，返回默认Cookie
            print(f"加载Cookie失败: {e}")
        
        # 如果Cookie文件损坏或不存在，返回默认Cookie
        return {"cookies": {}}
    
    async def get_works(self, account_id: int, page: int, page_size: int, earliest: str = None, latest: str = None) -> WorkListResponse:
        """获取作品列表"""
        # 加载设置
        loaded_settings = self._load_settings()
        
        # 查找账号（使用索引+1作为账号ID）
        account = None
        for i, acc in enumerate(loaded_settings["accounts"]):
            if i + 1 == account_id:
                account = acc
                break
        
        if not account:
            raise ValueError("账号不存在")
        
        # 加载Cookie
        loaded_cookie = self._load_cookie()
        
        # 解析账号URL获取用户ID
        user_id = self._extract_user_id(account["url"])
        if not user_id:
            raise ValueError("无效的账号URL")
        
        # 创建配置对象
        settings_obj = Settings(**loaded_settings)
        cookie_obj = Cookie()
        cookie_obj.cookies = loaded_cookie["cookies"]
        cleaner = Cleaner()
        
        # 解析日期
        from datetime import datetime
        if earliest and latest:
            # 使用前端传递的日期范围
            earliest_date = datetime.strptime(earliest, "%Y-%m-%d").date()
            latest_date = datetime.strptime(latest, "%Y-%m-%d").date()
        else:
            # 使用账号设置的日期范围
            earliest_date = datetime.strptime(account["earliest"], "%Y-%m-%d").date()
            latest_date = datetime.strptime(account["latest"], "%Y-%m-%d").date()
        
        # 获取作品列表
        acquire = Acquire()
        items = acquire.request_items(user_id, earliest_date, latest_date, settings_obj, cookie_obj)
        
        # 提取作品信息
        works = Parse.extract_items(items, earliest_date, latest_date, settings_obj, cleaner)
        
        # 分页
        start = (page - 1) * page_size
        end = start + page_size
        paginated_works = works[start:end]
        
        # 转换为响应模型
        work_responses = []
        for work in paginated_works:
            # 处理create_time的不同类型
            create_time_value = work["create_time"]
            if isinstance(create_time_value, str):
                try:
                    # 尝试解析日期字符串
                    create_time = datetime.strptime(create_time_value, "%Y-%m-%d")
                except ValueError:
                    # 如果解析失败，使用当前时间
                    create_time = datetime.now()
            elif isinstance(create_time_value, (int, float)):
                # 如果是时间戳，转换为datetime
                create_time = datetime.fromtimestamp(create_time_value)
            else:
                # 其他情况，使用当前时间
                create_time = datetime.now()
            
            work_response = WorkResponse(
                id=work["id"],
                desc=work["desc"],
                create_time=create_time,
                type=work["type"],
                width=work["width"],
                height=work["height"],
                downloads=work["downloads"] if isinstance(work["downloads"], list) else [work["downloads"]] if work["downloads"] else [],
                cover_url=work.get("cover_url", ""),
                account_id=account_id,
                account_mark=account["mark"]
            )
            work_responses.append(work_response)
        
        # 构建响应
        response = WorkListResponse(
            items=work_responses,
            total=len(works),
            page=page,
            page_size=page_size,
            has_more=end < len(works)
        )
        
        return response
    
    async def get_work(self, work_id: str) -> Optional[WorkResponse]:
        """获取单个作品"""
        # 加载设置
        loaded_settings = self._load_settings()
        
        # 遍历所有账号，查找作品
        for i, account in enumerate(loaded_settings["accounts"]):
            # 使用索引+1作为账号ID
            account_id = i + 1
            
            # 解析账号URL获取用户ID
            user_id = self._extract_user_id(account["url"])
            if not user_id:
                continue
            
            # 加载Cookie
            loaded_cookie = self._load_cookie()
            
            # 创建配置对象
            settings_obj = Settings(**loaded_settings)
            cookie_obj = Cookie()
            cookie_obj.cookies = loaded_cookie["cookies"]
            cleaner = Cleaner()
            
            # 解析日期
            from datetime import datetime
            earliest = datetime.strptime(account["earliest"], "%Y-%m-%d").date()
            latest = datetime.strptime(account["latest"], "%Y-%m-%d").date()
            
            # 获取作品列表
            acquire = Acquire()
            items = acquire.request_items(user_id, earliest, latest, settings_obj, cookie_obj)
            
            # 提取作品信息
            works = Parse.extract_items(items, earliest, latest, settings_obj, cleaner)
            
            # 查找作品
            for work in works:
                if work["id"] == work_id:
                    # 处理create_time的不同类型
                    create_time_value = work["create_time"]
                    if isinstance(create_time_value, str):
                        try:
                            # 尝试解析日期字符串
                            create_time = datetime.strptime(create_time_value, "%Y-%m-%d")
                        except ValueError:
                            # 如果解析失败，使用当前时间
                            create_time = datetime.now()
                    elif isinstance(create_time_value, (int, float)):
                        # 如果是时间戳，转换为datetime
                        create_time = datetime.fromtimestamp(create_time_value)
                    else:
                        # 其他情况，使用当前时间
                        create_time = datetime.now()
                    
                    # 转换为响应模型
                    work_response = WorkResponse(
                        id=work["id"],
                        desc=work["desc"],
                        create_time=create_time,
                        type=work["type"],
                        width=work["width"],
                        height=work["height"],
                        downloads=work["downloads"] if isinstance(work["downloads"], list) else [work["downloads"]] if work["downloads"] else [],
                        cover_url=work.get("cover_url", ""),
                        account_id=account_id,
                        account_mark=account["mark"]
                    )
                    return work_response
        
        return None
    
    async def download_selected_works(self, work_ids: List[str]) -> dict:
        """下载选中的作品"""
        # 加载设置
        loaded_settings = self._load_settings()
        
        # 加载Cookie
        loaded_cookie = self._load_cookie()
        
        # 遍历所有账号，查找作品
        selected_works = []
        for i, account in enumerate(loaded_settings["accounts"]):
            # 使用索引+1作为账号ID
            account_id = i + 1
            
            # 解析账号URL获取用户ID
            user_id = self._extract_user_id(account["url"])
            if not user_id:
                continue
            
            # 创建配置对象
            settings_obj = Settings(**loaded_settings)
            cookie_obj = Cookie()
            cookie_obj.cookies = loaded_cookie["cookies"]
            cleaner = Cleaner()
            
            # 解析日期
            from datetime import datetime
            earliest = datetime.strptime(account["earliest"], "%Y-%m-%d").date()
            latest = datetime.strptime(account["latest"], "%Y-%m-%d").date()
            
            # 获取作品列表
            acquire = Acquire()
            items = acquire.request_items(user_id, earliest, latest, settings_obj, cookie_obj)
            
            # 提取作品信息
            works = Parse.extract_items(items, earliest, latest, settings_obj, cleaner)
            
            # 查找选中的作品
            for work in works:
                if work["id"] in work_ids:
                    # 添加账号信息
                    work["account_id"] = account_id
                    work["account_mark"] = account["mark"]
                    selected_works.append(work)
        
        if not selected_works:
            raise ValueError("未找到选中的作品")
        
        # 开始下载
        from src.download.download import Download
        
        # 下载作品
        Download.download_items(selected_works, settings_obj, cookie_obj, cleaner)
        
        return {"message": f"已开始下载 {len(selected_works)} 个作品"}
    
    def _extract_user_id(self, url: str) -> Optional[str]:
        """从URL中提取用户ID"""
        import re
        # 匹配抖音用户URL
        match = re.search(r"douyin\.com/(user|account)/([a-zA-Z0-9_-]+)", url)
        if match:
            return match.group(2)
        # 匹配抖音分享URL
        match = re.search(r"v\.douyin\.com/([a-zA-Z0-9_-]+)", url)
        if match:
            # 这里需要解析短链接，暂时返回空
            return None
        return None
