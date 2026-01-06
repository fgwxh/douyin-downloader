from rich.progress import (
    SpinnerColumn,
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
)
from pathlib import Path
from rich import print
from urllib.parse import urlencode
from requests import get, exceptions
from time import sleep
from random import randint

from ..config import Settings, Cookie, Colors, HEADERS
from ..tool import Cleaner, retry


class Download:
    @staticmethod
    def _create_save_folder(id: str, mark: str, settings: Settings):
        '''新建存储文件夹，返回文件夹路径'''
        folder = settings.save_folder / f'UID{id}_{mark}_发布作品'
        folder.mkdir(exist_ok=True, parents=True)
        return folder

    @staticmethod
    def _generate_task_image(id: str, desc: str, name: str, index: int, url: str, width: int, height: int, save_folder: Path):
        '''生成图片下载任务信息'''
        show = f'图集 {id} {desc[:15]}'
        if (path := save_folder / f'{name}_{index}.jpeg').exists():
            print(f'[{Colors.CYAN}]{show} 文件已存在，跳过下载')
        else:
            return (url, path, show, id, width, height)

    @staticmethod
    def _generate_task_video(id: str, desc: str, name: str, format: str, url: str, width: int, height: int, save_folder: Path):
        '''生成视频下载任务信息'''
        show = f'视频 {id} {desc[:15]}'
        if (path := save_folder / f'{name}{format}').exists():
            print(f'[{Colors.CYAN}]{show} 文件已存在，跳过下载')
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
                        id, desc, name, index, info[0], info[1], info[2], save_folder)) is not None:
                        tasks.append(task)
            elif type == '视频':
                url = item['downloads']
                width = item['width']
                height = item['height']
                if (task := Download._generate_task_video(
                    id, desc, name, format, url, width, height, save_folder)) is not None:
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
        with open(path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=settings.chunk_size):
                f.write(chunk)
                progress.update(task_id, advance=len(chunk))
        progress.remove_task(task_id)
        if max(width, height) < 1920:
            color = Colors.YELLOW
        else:
            color = Colors.GREEN
        print(f'[{Colors.GREEN}]{show} [{color}]清晰度：{width}×{height}[{Colors.GREEN}] 下载完成 ({path.stat().st_size / (1024 * 1024):.2f} MB)')

    @staticmethod
    @retry
    def _request_file(url: str, path: Path, show: str, id: str, width: int, height: int,
                            progress: Progress, settings: Settings, cookie: Cookie):
        '''下载 url 对应文件'''
        # 测试网络连接
        print(f'[{Colors.CYAN}]{show} 开始测试网络连接...')
        import socket
        def test_connection(host, port=443, timeout=5):
            try:
                with socket.create_connection((host, port), timeout=timeout):
                    return True
            except:
                return False
        
        # 测试DNS解析
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        host = parsed_url.netloc
        print(f'[{Colors.CYAN}]{show} 测试连接到: {host}')
        
        if test_connection(host):
            print(f'[{Colors.GREEN}]{show} 网络连接测试成功')
        else:
            print(f'[{Colors.YELLOW}]{show} 网络连接测试失败，请检查网络连接')
        
        # 尝试使用不同的请求头
        print(f'[{Colors.CYAN}]{show} 尝试下载...')
        
        # 使用不同的用户代理
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'Mozilla/5.0 (Linux; Android 14; SM-S901U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36'
        ]
        
        # 尝试不同的用户代理
        for i, ua in enumerate(user_agents):
            print(f'[{Colors.CYAN}]{show} 尝试使用用户代理 [{i+1}/{len(user_agents)}]: {ua[:50]}...')
            
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
                print(f'[{Colors.CYAN}]{show} 尝试无代理连接...')
                response = get(
                    url,
                    timeout=settings.timeout,
                    headers=headers,
                    stream=True,
                    proxies=None
                )
                
                # 检查响应状态码
                print(f'[{Colors.CYAN}]{show} 响应状态码: {response.status_code}')
                
                if response.status_code == 200 or response.status_code == 206:
                    # 检查内容长度
                    content_length = int(response.headers.get('content-length', 0))
                    print(f'[{Colors.CYAN}]{show} 内容长度: {content_length} bytes')
                    
                    if content_length > 0:
                        # 下载文件
                        print(f'[{Colors.GREEN}]{show} 开始下载文件...')
                        Download._save_file(path, show, id, width, height,
                                          response, content_length, progress, settings)
                        
                        # 检查文件是否为空
                        if path.exists() and path.stat().st_size > 0:
                            print(f'[{Colors.GREEN}]{show} 下载成功！文件大小: {path.stat().st_size / (1024 * 1024):.2f} MB')
                            return True
                        else:
                            print(f'[{Colors.RED}]{show} 下载的文件为空，删除文件')
                            if path.exists():
                                path.unlink()
                            continue
                    
            except exceptions.ReadTimeout:
                print(f'[{Colors.YELLOW}]{show} 响应超时')
            except (exceptions.ProxyError, exceptions.SSLError, exceptions.ConnectionError) as e:
                print(f'[{Colors.YELLOW}]{show} 网络异常: {str(e)}')
            except Exception as e:
                print(f'[{Colors.RED}]{show} 下载时发生未知错误: {str(e)}')
            
            # 尝试使用代理
            if hasattr(settings, 'proxy') and settings.proxy:
                try:
                    print(f'[{Colors.CYAN}]{show} 尝试使用代理连接...')
                    response = get(
                        url,
                        timeout=settings.timeout,
                        headers=headers,
                        stream=True,
                        proxies={'http': settings.proxy, 'https': settings.proxy}
                    )
                    
                    # 检查响应状态码
                    print(f'[{Colors.CYAN}]{show} 代理响应状态码: {response.status_code}')
                    
                    if response.status_code == 200 or response.status_code == 206:
                        # 检查内容长度
                        content_length = int(response.headers.get('content-length', 0))
                        print(f'[{Colors.CYAN}]{show} 代理内容长度: {content_length} bytes')
                        
                        if content_length > 0:
                            # 下载文件
                            print(f'[{Colors.GREEN}]{show} 开始使用代理下载文件...')
                            Download._save_file(path, show, id, width, height,
                                              response, content_length, progress, settings)
                            
                            # 检查文件是否为空
                            if path.exists() and path.stat().st_size > 0:
                                print(f'[{Colors.GREEN}]{show} 代理下载成功！文件大小: {path.stat().st_size / (1024 * 1024):.2f} MB')
                                return True
                            else:
                                print(f'[{Colors.RED}]{show} 代理下载的文件为空，删除文件')
                                if path.exists():
                                    path.unlink()
                except exceptions.ProxyError as e:
                    print(f'[{Colors.YELLOW}]{show} 代理连接失败: {str(e)}')
                except Exception as e:
                    print(f'[{Colors.RED}]{show} 代理下载时发生错误: {str(e)}')
        
        # 清理可能创建的空文件
        if path.exists() and path.stat().st_size == 0:
            print(f'[{Colors.RED}]{show} 下载失败，删除空文件')
            path.unlink()
        
        sleep(randint(10, 30)/10)
        return False

    @staticmethod
    def _download_file(task_info: tuple, progress: Progress,
                             settings: Settings, cookie: Cookie):
        Download._request_file(*task_info, progress, settings, cookie)

    @staticmethod
    def _download_files(tasks_info: list, progress: Progress, settings: Settings, cookie: Cookie):
        for task_info in tasks_info:
            Download._download_file(task_info, progress, settings, cookie)

    @staticmethod
    def download_files(items: list[dict], account_id: str, account_mark: str,
                       settings: Settings, cleaner: Cleaner, cookie: Cookie):
        '''下载作品文件'''
        print(f'[{Colors.CYAN}]\n开始下载作品文件\n')
        save_folder = Download._create_save_folder(account_id, account_mark, settings)
        tasks_info = Download._generate_task(items, save_folder, settings, cleaner)
        with Download._progress_object() as progress:
            Download._download_files(tasks_info, progress, settings, cookie)
