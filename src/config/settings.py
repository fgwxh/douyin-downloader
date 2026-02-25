from json import load
from json.decoder import JSONDecodeError
from re import match
from datetime import date, timedelta, datetime
from rich import print
from dataclasses import dataclass
from pathlib import Path
from os import name as os_name
import sys

PROJECT_ROOT = Path(__file__).parent.parent.parent
ENCODE = 'UTF-8-SIG' if os_name == 'nt' else 'UTF-8'
REFERER = 'https://www.douyin.com/'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
HEADERS = {'Referer': REFERER, 'User-Agent': USER_AGENT}
PHONE_USER_AGENT = 'com.ss.android.ugc.trill/494+Mozilla/5.0+(Linux;+Android+12;+2112123G+Build/SKQ1.211006.001;+wv)+AppleWebKit/537.36+(KHTML,+like+Gecko)+Version/4.0+Chrome/107.0.5304.105+Mobile+Safari/537.36'
RETRY_ACCOUNT: int = 3
RETRY_FILE: int = 2

class Colors:
    WHITE = '#aaaaaa'
    CYAN = 'bright_cyan'
    RED = 'bright_red'
    YELLOW = 'bright_yellow'
    GREEN = 'bright_green'
    MAGENTA = 'bright_magenta'


@dataclass
class Account:
    mark: str
    url: str
    earliest: str
    latest: str
    sec_user_id: str = None
    earliest_date: date = date(2016, 9, 20)
    latest_date: date = date.today() - timedelta(days=1)
    id: str = None
    name: str = None

    def __post_init__(self):
        self.sec_user_id = self._extract_sec_user_id()
        if self.earliest:
            self.earliest_date = self._generate_date_earliest()
        if self.latest:
            self.latest_date = self._generate_date_latest()

    def _extract_sec_user_id(self) -> str | None:
        if not self.url:
            print(f'[{Colors.RED}]参数 accounts 中账号 {self.mark} 的 url 为空，提取 sec_user_id 失败！')
            return None
        
        # 处理包含sec_user_id参数的URL
        if 'sec_user_id=' in self.url:
            return self.url.split('sec_user_id=')[1].split('&')[0]
        
        # 处理普通用户URL格式 https://www.douyin.com/user/xxx
        match_url = match(r'https://www\.douyin\.com/user/([A-Za-z0-9_-]+)(\?.*)?', self.url)
        if match_url:
            return match_url.group(1)
        
        # 处理无www前缀的URL
        match_url = match(r'https://douyin\.com/user/([A-Za-z0-9_-]+)(\?.*)?', self.url)
        if match_url:
            return match_url.group(1)
        
        # 处理短链接格式
        match_url = match(r'https://v\.douyin\.com/[A-Za-z0-9]+', self.url)
        if match_url:
            print(f'[{Colors.YELLOW}]参数 accounts 中账号 {self.mark} 的 url 是短链接格式，需要手动解析 sec_user_id')
            return None
        
        print(f'[{Colors.RED}]参数 accounts 中账号 {self.mark} 的 url {self.url} 格式错误，提取 sec_user_id 失败！')
        return None

    def _generate_date_earliest(self) -> date:
        try:
            return datetime.strptime(self.earliest, '%Y/%m/%d').date()
        except ValueError:
            print(f'[{Colors.YELLOW}]作品最早发布日期 {self.earliest} 无效')
            return self.earliest_date

    def _generate_date_latest(self) -> date:
        try:
            return datetime.strptime(self.latest, '%Y/%m/%d').date()
        except ValueError:
            print(f'[{Colors.YELLOW}]作品最晚发布日期无效 {self.latest}')
            return self.latest_date


@dataclass(frozen=True)
class Settings:
    accounts: tuple[Account]
    save_folder: Path = PROJECT_ROOT
    download_videos: bool = True
    download_images: bool = False
    name_format: tuple[str] = ('create_time', 'id', 'type', 'desc')
    split: str = '-'
    date_format: str = '%Y-%m-%d'
    proxy: str = None
    file_description_max_length: int = 64
    chunk_size: int = 1024 * 1024
    timeout: int = 60 * 5
    concurrency: int = 5


def load_settings() -> Settings:
    # 优先检查 ./data/settings_mine.json（与app.py中的保存位置一致）
    data_settings = PROJECT_ROOT / 'data' / 'settings_mine.json'
    root_settings = PROJECT_ROOT / 'settings_mine.json'
    
    if data_settings.exists():
        filepath = data_settings
    elif root_settings.exists():
        filepath = root_settings
    else:
        filepath = PROJECT_ROOT / 'settings_default.json'
    
    try:
        with open(filepath, encoding=ENCODE) as f:
            data = load(f)
        print(f'[{Colors.GREEN}]成功加载配置文件: {filepath}')
    except JSONDecodeError:
        print(f'[{Colors.RED}]配置文件 {filepath.name} 格式错误，请检查 JSON 格式！')
        sys.exit()
    except Exception as e:
        print(f'[{Colors.RED}]加载配置文件 {filepath.name} 失败: {str(e)}')
        sys.exit()

    accounts = tuple(Account(**a) for a in data["accounts"])
    data_without_accounts = {k: v for k, v in data.items() if k != "accounts"}
    if 'save_folder' in data_without_accounts:
        data_without_accounts['save_folder'] = Path(data_without_accounts.get('save_folder'))
    if 'name_format' in data_without_accounts:
        data_without_accounts['name_format'] = tuple(data_without_accounts.get('name_format'))
    return Settings(accounts=accounts, **data_without_accounts)


if __name__ == '__main__':
    print(load_settings())
    input()
