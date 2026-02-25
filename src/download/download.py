from rich.progress import (
    SpinnerColumn,
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
)
from pathlib import Path
from urllib.parse import urlparse
from requests import get, exceptions
from time import sleep
from random import randint

from ..config import Settings, Cookie, Colors, HEADERS
from ..tool import Cleaner, retry, logger


class Download:
    @staticmethod
    def _create_save_folder(id: str, mark: str, settings: Settings):
        '''新建存储文件夹，返回文件夹路径'''
        folder = settings.save_folder / f'UID{id}_{mark}_发布作品'
        folder.mkdir(exist_ok=True, parents=True)
        return folder

    @staticmethod
    def _generate_task_image(id: str, desc: str, name: str, index: int, url: str, width: int, height: int, save_folder: Path, settings: Settings):
        '''生成图片下载任务信息'''
        show = f'图集 {id} {desc[:15]}'
        # 检查作品是否已经在本地存在
        if Download._is_work_exists(id, settings):
            logger.info(f'{show} 作品已在本地存在，跳过下载')
            return None
        # 检查当前文件夹中是否已经存在该文件
        if (path := save_folder / f'{name}_{index}.jpeg').exists():
            logger.info(f'{show} 文件已存在，跳过下载')
        else:
            return (url, path, show, id, width, height)

    @staticmethod
    def _is_work_exists(id: str, settings: Settings):
        '''检查作品是否已经在本地存在'''
        # 遍历所有账号的保存文件夹
        for account in settings.accounts:
            # 获取账号ID，处理字典和对象两种情况
            account_id = getattr(account, 'id', None) or account.get('id') if isinstance(account, dict) else None
            # 获取账号标识，处理字典和对象两种情况
            account_mark = getattr(account, 'mark', '') or account.get('mark', '') if isinstance(account, dict) else ''
            # 创建保存文件夹路径
            account_folder = settings.save_folder / f'UID{account_id or "unknown"}_{account_mark}_发布作品'
            if not account_folder.exists():
                continue
            # 遍历文件夹中的所有文件
            for file_path in account_folder.iterdir():
                if file_path.is_file():
                    # 检查文件名中是否包含作品ID
                    if id in file_path.name:
                        return True
        return False

    @staticmethod
    def _generate_task_video(id: str, desc: str, name: str, format: str, url: str, width: int, height: int, save_folder: Path, settings: Settings):
        '''生成视频下载任务信息'''
        show = f'视频 {id} {desc[:15]}'
        # 检查作品是否已经在本地存在
        if Download._is_work_exists(id, settings):
            logger.info(f'{show} 作品已在本地存在，跳过下载')
            return None
        # 检查当前文件夹中是否已经存在该文件
        if (path := save_folder / f'{name}{format}').exists():
            logger.info(f'{show} 文件已存在，跳过下载')
            return None
        else:
            return (url, path, show, id, width, height)

    @staticmethod
    def _generate_task(items: list[dict], save_folder: Path, settings: Settings, cleaner: Cleaner):
        '''生成下载任务信息列表并返回'''
        tasks = []
        for item in items:
            id = item['id']
            desc = item['desc']
            name = cleaner.filter_name(settings.split.join(
                item[key] for key in settings.name_format))
            format = item.get('format') # 图片任务解析时没有提取字段，在下面直接设置为 .jpeg
            if (type := item['type']) == '图集':
                for index, info in enumerate(item['downloads'], start=1):
                    if (task := Download._generate_task_image(
                        id, desc, name, index, info[0], info[1], info[2], save_folder, settings)) is not None:
                        tasks.append(task)
            elif type == '视频':
                url = item['downloads']
                width = item['width']
                height = item['height']
                if (task := Download._generate_task_video(
                    id, desc, name, format, url, width, height, save_folder, settings)) is not None:
                    tasks.append(task)
        return tasks

    @staticmethod
    def _progress_object():
        return Progress(
            TextColumn('[progress.description]{task.description}', style=Colors.MAGENTA, justify='left'),
            SpinnerColumn(),
            BarColumn(bar_width=20),
            '[progress.percentage]{task.percentage:>3.1f}%',
            '•',
            DownloadColumn(binary_units=True),
            '•',
            TimeRemainingColumn(),
            transient=True,
        )

    @staticmethod
    def _save_file(path: Path, show: str, id: str, width: int, height: int,
                         response, content_length: int, progress: Progress, settings: Settings):
        task_id = progress.add_task(show, total=content_length or None)
        downloaded = 0
        with open(path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=settings.chunk_size):
                f.write(chunk)
                downloaded += len(chunk)
                progress.update(task_id, advance=len(chunk))
        progress.remove_task(task_id)
        
        # 计算文件大小（使用二进制单位）
        file_size_mib = path.stat().st_size / (1024 * 1024)
        
        # 比较下载的大小与 content-length
        if content_length > 0 and abs(downloaded - content_length) > 1024:  # 允许 1KB 差异
            expected_size_mib = content_length / (1024 * 1024)
            logger.warning(f'{show} 下载大小与预期不符：预期 {expected_size_mib:.2f} MiB，实际 {file_size_mib:.2f} MiB')
        
        if max(width, height) < 1920:
            color = Colors.YELLOW
        else:
            color = Colors.GREEN
        logger.success(f'{show} [{color}]清晰度：{width}×{height}[/{color}] 下载完成 ({file_size_mib:.2f} MiB)')

    @staticmethod
    @retry
    def _request_file(url: str, path: Path, show: str, id: str, width: int, height: int,
                            progress: Progress, settings: Settings, cookie: Cookie):
        '''下载 url 对应文件'''
        # 使用不同的用户代理
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'Mozilla/5.0 (Linux; Android 14; SM-S901U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36'
        ]
        
        # 尝试不同的用户代理
        for i, ua in enumerate(user_agents):
            # 构建请求头
            headers = {
                'Referer': 'https://www.douyin.com/',
                'User-Agent': ua,
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Connection': 'keep-alive'
            }
            
            # 添加Cookie
            if cookie.cookies:
                headers['Cookie'] = cookie._generate_str()
            
            try:
                # 尝试无代理连接
                response = get(
                    url,
                    timeout=settings.timeout,
                    headers=headers,
                    stream=True,
                    proxies=None
                )
                
                if response.status_code == 200 or response.status_code == 206:
                    # 检查内容长度
                    content_length = int(response.headers.get('content-length', 0))
                    
                    if content_length > 0:
                        # 下载文件
                        Download._save_file(path, show, id, width, height,
                                          response, content_length, progress, settings)
                        
                        # 检查文件是否为空
                        if path.exists() and path.stat().st_size > 0:
                            file_size_mib = path.stat().st_size / (1024 * 1024)
                            logger.success(f'{show} 下载成功！文件大小: {file_size_mib:.2f} MiB')
                            return True
                        else:
                            if path.exists():
                                path.unlink()
                            continue
                    
            except exceptions.ReadTimeout:
                pass
            except (exceptions.ProxyError, exceptions.SSLError, exceptions.ConnectionError):
                pass
            except Exception:
                pass
            
            # 尝试使用代理
            if hasattr(settings, 'proxy') and settings.proxy:
                try:
                    response = get(
                        url,
                        timeout=settings.timeout,
                        headers=headers,
                        stream=True,
                        proxies={'http': settings.proxy, 'https': settings.proxy}
                    )
                    
                    if response.status_code == 200 or response.status_code == 206:
                        # 检查内容长度
                        content_length = int(response.headers.get('content-length', 0))
                        
                        if content_length > 0:
                            # 下载文件
                            Download._save_file(path, show, id, width, height,
                                            response, content_length, progress, settings)
                            
                            # 检查文件是否为空
                            if path.exists() and path.stat().st_size > 0:
                                file_size_mib = path.stat().st_size / (1024 * 1024)
                                logger.success(f'{show} 下载成功！文件大小: {file_size_mib:.2f} MiB')
                                return True
                            else:
                                if path.exists():
                                    path.unlink()
                                continue
                                
                except (exceptions.ProxyError, exceptions.SSLError, exceptions.ConnectionError):
                    pass
                except Exception:
                    pass
            
            # 随机等待
            sleep(randint(1, 3))
        
        # 所有尝试都失败
        logger.error(f'{show} 下载失败')
        if path.exists() and path.stat().st_size == 0:
            path.unlink()
        return False

    @staticmethod
    def download_items(items: list[dict], settings: Settings, cookie: Cookie, cleaner: Cleaner):
        '''下载作品文件'''
        if not items:
            logger.warning('没有需要下载的作品')
            return
        
        logger.info(f'\n开始下载 {len(items)} 个选中的作品...\n')
        
        # 创建保存文件夹
        if items:
            first_item = items[0]
            save_folder = Download._create_save_folder(
                first_item.get('account_id', 'unknown'),
                first_item.get('account_mark', '未命名'),
                settings
            )
        
        # 生成下载任务
        tasks = Download._generate_task(items, save_folder, settings, cleaner)
        
        if not tasks:
            logger.info('所有作品都已存在，无需下载')
            return
        
        logger.info(f'生成 {len(tasks)} 个下载任务\n')
        
        # 开始下载
        with Download._progress_object() as progress:
            success_count = 0
            fail_count = 0
            
            for task in tasks:
                url, path, show, id, width, height = task
                if Download._request_file(url, path, show, id, width, height, progress, settings, cookie):
                    success_count += 1
                else:
                    fail_count += 1
                
                # 下载间隔
                sleep(randint(2, 5))
            
            # 显示统计
            logger.info(f'\n下载完成！成功: {success_count} 个，失败: {fail_count} 个')
