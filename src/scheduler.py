from rich.prompt import Prompt
from textwrap import dedent
import subprocess
from time import sleep
from random import randint

from .config import Account, load_settings, Cookie, Colors, PROJECT_ROOT
from .tool import Cleaner, logger
from .download import Acquire, Download, Parse


class Scheduler:
    def __init__(self) -> None:
        self.settings = load_settings()
        self.cookie = Cookie()
        self.cleaner = Cleaner()
        self.test_network_connection()
    
    def test_network_connection(self):
        """测试网络连接并自动切换代理设置"""
        import requests
        test_url = "https://www.douyin.com"
        
        try:
            # 尝试无代理连接
            test_response = requests.get(test_url, timeout=10, proxies=None)
            
            # 如果无代理连接成功，禁用代理
            if self.settings.proxy:
                # 创建一个新的Settings对象，禁用代理
                from .config import Settings
                temp_settings_dict = {}
                for attr in dir(self.settings):
                    if not attr.startswith('_'):
                        temp_settings_dict[attr] = getattr(self.settings, attr)
                temp_settings_dict['proxy'] = None
                self.settings = Settings(**temp_settings_dict)
                
        except Exception:
            # 尝试使用代理连接
            if self.settings.proxy:
                try:
                    test_response = requests.get(test_url, timeout=10, proxies={'http': self.settings.proxy, 'https': self.settings.proxy})
                except Exception:
                    pass

    def _deal_account(self, num: int, account: Account):
        for i in (
            f'\n开始处理第 {num} 个账号' if num else '开始处理账号',
            f'账号标识：{account.mark or "空"}',
            f'最早发布日期：{account.earliest or "空"}，最晚发布日期：{account.latest or "空"}'
        ):
            logger.info(i)
        items = Acquire().request_items(account.sec_user_id, account.earliest_date, self.settings, self.cookie)
        if items:
            logger.info('\n开始提取作品数据')
            Parse.extract_account(account, items[0], self.cleaner)
            logger.info(f'账号昵称：{account.name}；账号 ID：{account.id}')
            items = Parse.extract_items(items, account.earliest_date, account.latest_date,
                                        self.settings, self.cleaner)
            logger.info(f'当前账号作品数量: {len(items)}')
            Download.download_files(items, account.id, account.mark,
                                    self.settings, self.cleaner, self.cookie)
            return True

    def _deal_accounts(self):
        accounts = self.settings.accounts
        logger.info(f'共有 {len(accounts)} 个账号的作品等待下载')
        for num, account in enumerate(accounts, start=1):
            if num % 5 == 0:
                sleep_time = randint(20, 180)
                logger.info(f'已处理 {num-1} 个账号，等待 {sleep_time} 秒后继续')
                sleep(sleep_time)
            self.cookie.update()
            self._deal_account(num, account)

    def run(self):
        tips = dedent(
            f'''
            {'='*25}
            1. 复制粘贴写入 Cookie
            2. 修改配置文件(Linux)
            {'='*25}
            3. 批量下载账号作品(配置文件)
            {'='*25}

            请选择运行模式：''')
        while (mode := Prompt.ask(f'[{Colors.CYAN}]{tips}', choices=['q', '1', '2', '3'], default='3')) != 'q':
            if mode == '1':
                self.cookie.input_save()
            elif mode == '2':
                if not (filepath := PROJECT_ROOT / 'settings_mine.json').exists():
                    filepath = PROJECT_ROOT / 'settings_default.json'
                subprocess.run(['xdg-open', str(filepath)])
                try:
                    subprocess.run(['xdg-open', str(PROJECT_ROOT / '已下载账号信息.json')])
                except:
                    pass
                input()
                self.settings = load_settings()
            elif mode == '3':
                self.cookie.load_cookies()
                self._deal_accounts()
        logger.info('程序结束运行', color=Colors.WHITE)
    
    def run_download(self):
        """直接执行下载任务，不显示交互式菜单"""
        self.cookie.load_cookies()
        self._deal_accounts()
