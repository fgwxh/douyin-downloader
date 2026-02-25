from typing import Dict, Optional
from app.schemas.download import DownloadRequest, DownloadResponse, DownloadStatus
from app.core.config import settings
import json
from pathlib import Path
import asyncio
import uuid
from datetime import datetime
from src.download.download import Download
from src.config import Settings, Cookie
from src.tool.cleaner import Cleaner
from src.tool import logger

class DownloadService:
    """下载服务"""
    
    # 类变量，所有实例共享
    download_tasks: Dict[str, Dict] = {}
    
    def __init__(self):
        """初始化下载服务"""
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
            from pathlib import Path
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
    
    async def start_download(self, download_request: DownloadRequest) -> DownloadResponse:
        """开始下载任务"""
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 使用线程池执行同步操作，避免阻塞事件循环
        loop = asyncio.get_event_loop()
        
        # 加载设置
        loaded_settings = await loop.run_in_executor(None, self._load_settings)
        
        # 查找账号
        account = None
        for i, acc in enumerate(loaded_settings["accounts"]):
            # 使用索引+1作为账号ID
            account_id = i + 1
            if account_id == download_request.account_id:
                account = acc
                # 添加账号ID
                account["id"] = account_id
                break
        
        if not account:
            raise ValueError("账号不存在")
        
        # 加载Cookie
        loaded_cookie = await loop.run_in_executor(None, self._load_cookie)
        
        # 创建配置对象
        # 确保save_folder是Path对象
        if "save_folder" in loaded_settings and isinstance(loaded_settings["save_folder"], str):
            from pathlib import Path
            loaded_settings["save_folder"] = Path(loaded_settings["save_folder"])
        settings_obj = Settings(**loaded_settings)
        cookie_obj = Cookie()
        cookie_obj.cookies = loaded_cookie["cookies"]
        cleaner = Cleaner()
        
        # 初始化下载任务状态
        # 当work_ids为空时，total_count设置为-1，表示"未知数量"
        total_count = len(download_request.work_ids) if download_request.work_ids else -1
        DownloadService.download_tasks[task_id] = {
            "status": DownloadStatus.RUNNING.value,
            "message": "开始下载",
            "progress": 0.0,
            "completed_count": 0,
            "total_count": total_count,
            "start_time": datetime.now().isoformat()
        }
        
        # 启动后台下载任务
        asyncio.create_task(self._download_works(
            task_id, download_request.work_ids, account, settings_obj, cookie_obj, cleaner, download_request.works
        ))
        
        # 构建响应
        # 当work_ids为空时，total_count设置为-1，表示"未知数量"
        response_total_count = len(download_request.work_ids) if download_request.work_ids else -1
        response = DownloadResponse(
            task_id=task_id,
            status=DownloadStatus.RUNNING,
            message="开始下载",
            progress=0.0,
            completed_count=0,
            total_count=response_total_count
        )
        
        return response
    
    async def _download_works(self, task_id: str, work_ids: list, account: dict, 
                            settings_obj: Settings, cookie_obj: Cookie, cleaner: Cleaner, works: list = None):
        """下载作品"""
        try:
            # 使用线程池执行同步操作，避免阻塞事件循环
            loop = asyncio.get_event_loop()
            
            # 加载设置
            loaded_settings = await loop.run_in_executor(None, self._load_settings)
            
            # 解析账号URL获取用户ID
            user_id = self._extract_user_id(account["url"])
            if not user_id:
                DownloadService.download_tasks[task_id]["status"] = DownloadStatus.FAILED.value
                DownloadService.download_tasks[task_id]["message"] = "无效的账号URL"
                return
            
            # 解析日期
            from datetime import datetime
            from src.download.acquire import Acquire
            from src.download.parse import Parse
            
            earliest = datetime.strptime(account["earliest"], "%Y-%m-%d").date()
            latest = datetime.strptime(account["latest"], "%Y-%m-%d").date()
            
            # 检查是否有前端传递的作品信息
            if works and len(works) > 0:
                logger.info(f"使用前端传递的 {len(works)} 个作品信息，跳过作品列表获取")
                # 为视频作品添加format字段，并处理downloads字段
                for work in works:
                    if work.get("type") == "视频":
                        # 添加format字段
                        if "format" not in work:
                            work["format"] = ".mp4"
                            logger.info(f"为视频作品 {work.get('id')} 添加format字段: .mp4")
                        # 处理downloads字段，如果是列表，取第一个元素
                        if isinstance(work.get("downloads"), list) and work.get("downloads"):
                            work["downloads"] = work["downloads"][0]
                            logger.info(f"为视频作品 {work.get('id')} 处理downloads字段，取第一个元素")
            else:
                # 检查是否有指定的作品ID
                if work_ids:
                    # 如果有指定的作品ID，尝试从缓存中获取，或者直接构建作品信息
                    # 这里我们可以优化，比如使用缓存，或者直接通过API获取单个作品信息
                    # 但为了保持兼容性，暂时使用原有的实现
                    logger.info(f"正在获取指定的 {len(work_ids)} 个作品...")
                else:
                    logger.info("正在获取所有作品...")
                
                # 获取作品列表
                def get_items():
                    try:
                        acquire = Acquire()
                        return acquire.request_items(user_id, earliest, latest, settings_obj, cookie_obj)
                    except Exception as e:
                        logger.error(f"获取作品列表失败: {str(e)}")
                        return None
                
                items = await loop.run_in_executor(None, get_items)
                
                if not items:
                    DownloadService.download_tasks[task_id]["status"] = DownloadStatus.FAILED.value
                    DownloadService.download_tasks[task_id]["message"] = "获取作品列表失败"
                    return
                
                # 提取作品信息
                def extract_works():
                    return Parse.extract_items(items, earliest, latest, settings_obj, cleaner)
                
                works = await loop.run_in_executor(None, extract_works)
            
            # 筛选选中的作品
            selected_works = []
            for work in works:
                # 如果work_ids为空，下载所有作品
                if not work_ids or work["id"] in work_ids:
                    # 添加账号信息
                    work["account_id"] = account["id"]
                    work["account_mark"] = account["mark"]
                    selected_works.append(work)
            
            if not selected_works:
                DownloadService.download_tasks[task_id]["status"] = DownloadStatus.FAILED.value
                DownloadService.download_tasks[task_id]["message"] = "未找到选中的作品"
                return
            
            # 更新任务状态
            DownloadService.download_tasks[task_id]["total_count"] = len(selected_works)
            
            # 下载作品
            def download_items():
                Download.download_items(selected_works, settings_obj, cookie_obj, cleaner)
            
            await loop.run_in_executor(None, download_items)
            
            # 更新任务状态
            DownloadService.download_tasks[task_id]["status"] = DownloadStatus.COMPLETED.value
            DownloadService.download_tasks[task_id]["message"] = "下载完成"
            DownloadService.download_tasks[task_id]["progress"] = 100.0
            DownloadService.download_tasks[task_id]["completed_count"] = len(selected_works)
            
        except Exception as e:
            # 更新任务状态
            DownloadService.download_tasks[task_id]["status"] = DownloadStatus.FAILED.value
            DownloadService.download_tasks[task_id]["message"] = f"下载失败: {str(e)}"
    
    async def get_download_status(self, task_id: str) -> Optional[DownloadResponse]:
        """获取下载任务状态"""
        if task_id not in DownloadService.download_tasks:
            return None
        
        task = DownloadService.download_tasks[task_id]
        
        # 构建响应
        response = DownloadResponse(
            task_id=task_id,
            status=DownloadStatus(task["status"]),
            message=task.get("message", ""),
            progress=task.get("progress", 0.0),
            completed_count=task.get("completed_count", 0),
            total_count=task.get("total_count", 0)
        )
        
        return response
    
    async def stop_download(self, task_id: str) -> bool:
        """停止下载任务"""
        if task_id not in DownloadService.download_tasks:
            return False
        
        # 更新任务状态
        DownloadService.download_tasks[task_id]["status"] = DownloadStatus.FAILED.value
        DownloadService.download_tasks[task_id]["message"] = "下载已停止"
        
        return True
    
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
