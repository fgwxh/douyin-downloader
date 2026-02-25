import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.logging import RichHandler
from ..config import PROJECT_ROOT, Colors

# 日志目录
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

# 日志文件路径
LOG_FILE = LOG_DIR / "douyin_download.log"

# 创建全局Console对象
console = Console()

class Logger:
    """统一日志管理类"""
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._init_logger()
        return cls._instance
    
    def _init_logger(self):
        """初始化日志配置"""
        self.logger = logging.getLogger("douyin_download")
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False
        
        # 清除已有处理器
        self.logger.handlers.clear()
        
        # 1. Rich控制台输出处理器
        rich_handler = RichHandler(
            console=console,
            show_time=True,
            show_level=True,
            show_path=False,
            markup=True,
            rich_tracebacks=True
        )
        rich_handler.setLevel(logging.INFO)
        rich_format = logging.Formatter("%(message)s", datefmt="[%X]")
        rich_handler.setFormatter(rich_format)
        
        # 2. 文件输出处理器（滚动日志，最多保留10个日志文件，每个最大10MB）
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=10,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_format)
        
        # 添加处理器
        self.logger.addHandler(rich_handler)
        self.logger.addHandler(file_handler)
    
    def info(self, message, color=Colors.CYAN):
        """输出信息日志"""
        self.logger.info(f"[{color}]{message}[/{color}]")
    
    def success(self, message, color=Colors.GREEN):
        """输出成功日志"""
        self.logger.info(f"[{color}]✅ {message}[/{color}]")
    
    def warning(self, message, color=Colors.YELLOW):
        """输出警告日志"""
        self.logger.warning(f"[{color}]⚠️ {message}[/{color}]")
    
    def error(self, message, color=Colors.RED):
        """输出错误日志"""
        self.logger.error(f"[{color}]❌ {message}[/{color}]")
    
    def debug(self, message, color=Colors.WHITE):
        """输出调试日志"""
        self.logger.debug(f"[{color}]{message}[/{color}]")
    
    def print(self, message, color=None):
        """兼容原有print用法，直接输出"""
        if color:
            console.print(f"[{color}]{message}[/{color}]")
        else:
            console.print(message)
    
    def get_logs(self, lines: int = 1000):
        """获取最近的日志记录"""
        try:
            if LOG_FILE.exists():
                with open(LOG_FILE, 'r', encoding='utf-8', errors='replace') as f:
                    all_lines = f.readlines()
                    # 处理日志行，移除颜色标签并确保编码正确
                    processed_lines = []
                    for line in all_lines[-lines:]:
                        # 移除Rich颜色标签
                        line = line.replace('[bright_cyan]', '').replace('[/bright_cyan]', '')
                        line = line.replace('[bright_green]', '').replace('[/bright_green]', '')
                        line = line.replace('[bright_yellow]', '').replace('[/bright_yellow]', '')
                        line = line.replace('[bright_red]', '').replace('[/bright_red]', '')
                        line = line.replace('[#aaaaaa]', '').replace('[/#aaaaaa]', '')
                        # 移除图标
                        line = line.replace('✅ ', '').replace('⚠️ ', '').replace('❌ ', '')
                        # 移除换行符
                        processed_lines.append(line.rstrip('\n'))
                    return processed_lines
        except Exception as e:
            self.error(f"读取日志文件失败: {str(e)}")
        return []
    
    def clear_logs(self):
        """清空日志文件"""
        try:
            if LOG_FILE.exists():
                with open(LOG_FILE, 'w', encoding='utf-8') as f:
                    f.write('')
                self.info("日志已清空")
                return True
        except Exception as e:
            self.error(f"清空日志失败: {str(e)}")
        return False

# 全局日志实例
logger = Logger()
