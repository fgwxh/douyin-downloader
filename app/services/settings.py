from app.schemas.settings import SettingsUpdate, SettingsResponse
from app.core.config import settings
import json
from pathlib import Path

class SettingsService:
    """设置服务"""
    
    def __init__(self):
        """初始化设置服务"""
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
    
    async def get_settings(self) -> SettingsResponse:
        """获取当前设置"""
        # 加载设置
        loaded_settings = self._load_settings()
        
        # 构建响应
        response = SettingsResponse(
            id=1,  # 固定ID
            save_folder=loaded_settings.get("save_folder", "."),
            download_videos=loaded_settings.get("download_videos", True),
            download_images=loaded_settings.get("download_images", False),
            name_format=loaded_settings.get("name_format", ["create_time", "id", "type", "desc"]),
            split=loaded_settings.get("split", "-"),
            date_format=loaded_settings.get("date_format", "%Y-%m-%d"),
            proxy=loaded_settings.get("proxy", ""),
            file_description_max_length=loaded_settings.get("file_description_max_length", 64),
            chunk_size=loaded_settings.get("chunk_size", 1048576),
            timeout=loaded_settings.get("timeout", 300),
            concurrency=loaded_settings.get("concurrency", 5)
        )
        
        return response
    
    async def update_settings(self, settings_update: SettingsUpdate) -> SettingsResponse:
        """更新设置"""
        # 加载设置
        loaded_settings = self._load_settings()
        
        # 更新设置
        if settings_update.save_folder is not None:
            loaded_settings["save_folder"] = settings_update.save_folder
        if settings_update.download_videos is not None:
            loaded_settings["download_videos"] = settings_update.download_videos
        if settings_update.download_images is not None:
            loaded_settings["download_images"] = settings_update.download_images
        if settings_update.name_format is not None:
            loaded_settings["name_format"] = settings_update.name_format
        if settings_update.split is not None:
            loaded_settings["split"] = settings_update.split
        if settings_update.date_format is not None:
            loaded_settings["date_format"] = settings_update.date_format
        if settings_update.proxy is not None:
            loaded_settings["proxy"] = settings_update.proxy
        if settings_update.file_description_max_length is not None:
            loaded_settings["file_description_max_length"] = settings_update.file_description_max_length
        if settings_update.chunk_size is not None:
            loaded_settings["chunk_size"] = settings_update.chunk_size
        if settings_update.timeout is not None:
            loaded_settings["timeout"] = settings_update.timeout
        if settings_update.concurrency is not None:
            loaded_settings["concurrency"] = settings_update.concurrency
        
        # 保存设置
        self._save_settings(loaded_settings)
        
        # 构建响应
        response = SettingsResponse(
            id=1,  # 固定ID
            save_folder=loaded_settings.get("save_folder", "."),
            download_videos=loaded_settings.get("download_videos", True),
            download_images=loaded_settings.get("download_images", False),
            name_format=loaded_settings.get("name_format", ["create_time", "id", "type", "desc"]),
            split=loaded_settings.get("split", "-"),
            date_format=loaded_settings.get("date_format", "%Y-%m-%d"),
            proxy=loaded_settings.get("proxy", ""),
            file_description_max_length=loaded_settings.get("file_description_max_length", 64),
            chunk_size=loaded_settings.get("chunk_size", 1048576),
            timeout=loaded_settings.get("timeout", 300),
            concurrency=loaded_settings.get("concurrency", 5)
        )
        
        return response
