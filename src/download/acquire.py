from datetime import date
from urllib.parse import urlencode
from requests import exceptions, get
from rich.progress import (
    BarColumn,
    Progress,
    TextColumn,
    TimeElapsedColumn,
)
from random import randint
from time import sleep

from ..encrypt_params import get_a_bogus
from ..tool import retry, logger
from ..config import Settings, Colors, Cookie, HEADERS

POST_API = 'https://www.douyin.com/aweme/v1/web/aweme/post/'

class Acquire():

    def __init__(self):
        self.cursor = 0
        self.finished = False

    @staticmethod
    def _progress_object():
        return Progress(
            TextColumn('[progress.description]{task.description}', style=Colors.MAGENTA, justify='left'),
            '•',
            BarColumn(bar_width=20),
            '•',
            TimeElapsedColumn(),
            transient=True,
        )

    @staticmethod
    def _deal_url_params(params: dict, cookie: Cookie, number: int = 8):
        '''添加 msToken、X-Bogus'''
        if 'msToken' in cookie.cookies:
            params['msToken'] = cookie.cookies['msToken']
        params['a_bogus'] = get_a_bogus(params)

    @staticmethod
    def _wait():
        sleep(randint(15, 45)/10)

    @staticmethod
    @retry
    def _send_get(params, settings: Settings, cookie: Cookie):
        '''返回 json 格式数据'''
        # 优先尝试无代理连接获取作品数据
        logger.info('尝试无代理连接获取作品数据...')
        try:
            headers = HEADERS | {'Cookie': cookie._generate_str()}
            response = get(
                POST_API,
                params=params,
                timeout=settings.timeout,
                headers=headers,
                proxies=None
                )
            Acquire._wait()
            # 检查响应状态码
            if response.status_code == 200:
                logger.success('无代理连接成功')
                try:
                    return response.json()
                except exceptions.JSONDecodeError:
                    if response.text:
                        logger.warning(f'响应内容不是有效的 JSON 格式：{response.text[:100]}...')
                    else:
                        logger.warning('响应内容为空，可能是接口失效或者 Cookie 失效，请尝试更新 Cookie')
        except (
                exceptions.ProxyError,
                exceptions.SSLError,
                exceptions.ChunkedEncodingError,
                exceptions.ConnectionError,
        ):
            logger.warning('无代理连接失败，尝试使用代理连接...')
        except exceptions.ReadTimeout:
            logger.warning('无代理连接超时，尝试使用代理连接...')
        
        # 如果无代理连接失败，尝试使用代理连接
        if hasattr(settings, 'proxy') and settings.proxy:
            logger.info('尝试使用代理连接获取作品数据...')
            try:
                headers = HEADERS | {'Cookie': cookie._generate_str()}
                response = get(
                    POST_API,
                    params=params,
                    timeout=settings.timeout,
                    headers=headers,
                    proxies={'http': settings.proxy, 'https': settings.proxy}
                    )
                Acquire._wait()
                # 检查响应状态码
                if response.status_code == 200:
                    logger.success('代理连接成功')
                    try:
                        return response.json()
                    except exceptions.JSONDecodeError:
                        if response.text:
                            logger.warning(f'响应内容不是有效的 JSON 格式：{response.text[:100]}...')
                        else:
                            logger.warning('响应内容为空，可能是接口失效或者 Cookie 失效，请尝试更新 Cookie')
            except (
                    exceptions.ProxyError,
                    exceptions.SSLError,
                    exceptions.ChunkedEncodingError,
                    exceptions.ConnectionError,
            ):
                logger.warning(f'网络异常，请求 {POST_API}?{urlencode(params)[:100]}... 失败')
            except exceptions.ReadTimeout:
                logger.warning(f'网络异常，请求 {POST_API}?{urlencode(params)[:100]}... 超时')
        
        return None

    def _get_cache_key(self, sec_user_id: str, earliest_date: date, latest_date: date) -> str:
        '''生成缓存键'''
        key_parts = [sec_user_id]
        if earliest_date:
            key_parts.append(str(earliest_date))
        if latest_date:
            key_parts.append(str(latest_date))
        return '_'.join(key_parts)
    
    def _load_cache(self, cache_key: str) -> list[dict] | None:
        '''加载缓存'''
        from pathlib import Path
        from datetime import datetime
        import json
        
        cache_dir = Path("./cache")
        cache_file = cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            try:
                # 检查缓存是否过期
                if (datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)).total_seconds() < 3600:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        return json.load(f)
            except Exception as e:
                logger.warning(f"加载缓存失败: {str(e)}")
        return None
    
    def _save_cache(self, cache_key: str, items: list[dict]):
        '''保存缓存'''
        from pathlib import Path
        import json
        
        cache_dir = Path("./cache")
        cache_dir.mkdir(exist_ok=True)
        cache_file = cache_dir / f"{cache_key}.json"
        
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(items, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"保存缓存失败: {str(e)}")
    
    def request_items(self, sec_user_id: str, earliest_date: date, latest_date: date, settings: Settings, cookie: Cookie) -> list[dict] | None:
        '''请求并返回所有作品数据'''
        try:
            # 生成缓存键
            cache_key = self._get_cache_key(sec_user_id, earliest_date, latest_date)
            
            # 尝试加载缓存
            cached_items = self._load_cache(cache_key)
            # 尝试加载缓存
            if cached_items:
                logger.info(f"从缓存中加载了 {len(cached_items)} 个作品")
                return cached_items
            
            items = []
            self.cursor = 0
            self.finished = False
            retry_count = 0
            max_retries = 3
            max_items = 1000  # 添加最大获取数量限制
            request_count = 0
            max_requests = 20  # 最大请求次数限制

            logger.info('开始获取作品列表...')
            logger.info(f'日期范围: {earliest_date} 到 {latest_date}')
            logger.info(f'最大获取数量: {max_items}')
            logger.info(f'最大请求次数: {max_requests}')
            
            while not self.finished and retry_count < max_retries and len(items) < max_items and request_count < max_requests:
                request_count += 1
                logger.info(f'第 {request_count} 次请求，cursor: {self.cursor}')
                
                # 构建完整的请求参数，包含必要的设备和应用信息
                params = {
                    'sec_user_id': sec_user_id,
                    'max_cursor': self.cursor,
                    'count': 100,  # 增加请求数量
                    'cut_version': 1,
                    'publish_video_strategy_type': 2,
                    'source': 'page',
                    'device_platform': 'webapp',
                    'aid': 6383,
                    'channel': 'channel_pc_web',
                    'pc_client_type': 1,
                    'version_code': 170400,
                    'version_name': '17.4.0',
                    'cookie_enabled': True,
                    'screen_width': 1536,
                    'screen_height': 864,
                    'browser_language': 'zh-CN',
                    'browser_platform': 'Win32',
                    'browser_name': 'Chrome',
                    'browser_version': '123.0.0.0',
                    'browser_online': True,
                    'engine_name': 'Blink',
                    'engine_version': '123.0.0.0',
                    'os_name': 'Windows',
                    'os_version': '10',
                    'cpu_core_num': 16,
                    'device_memory': 8,
                    'platform': 'PC',
                    'downlink': 10,
                    'effective_type': '4g',
                    'round_trip_time': 50,
                }
                
                # 添加msToken（如果存在）
                if 'msToken' in cookie.cookies:
                    params['msToken'] = cookie.cookies['msToken']
                
                # 添加a_bogus
                from src.encrypt_params import get_a_bogus
                params['a_bogus'] = get_a_bogus(params)

                if not (data := Acquire._send_get(params, settings, cookie)):
                    logger.warning('获取账号作品数据失败')
                    retry_count += 1
                    logger.info(f'第 {retry_count} 次重试...')
                    Acquire._wait()
                    continue

                status_code = data.get('status_code', 0)
                if status_code != 0:
                    status_msg = data.get('status_msg', '')
                    if '私密账号' in status_msg:
                        logger.warning('该账号为私密账号，需要使用登录后的 Cookie，且登录的账号需要关注该私密账号')
                        break
                    elif status_code == 5:
                        logger.warning(f'账号作品数据响应内容异常 (status_code=5): {str(data)[:100]}...')
                        logger.info('尝试重新获取作品列表...')
                        retry_count += 1
                        if retry_count < max_retries:
                            logger.info(f'第 {retry_count} 次重试...')
                            Acquire._wait()
                            continue
                        else:
                            logger.warning('达到最大重试次数，停止获取作品列表')
                            break
                    else:
                        logger.warning(f'账号作品数据响应内容异常 (status_code={status_code}): {str(data)[:100]}...')
                        break

                # 确保 max_cursor 正确更新
                old_cursor = self.cursor
                self.cursor = data.get('max_cursor', 0)
                self.finished = not data.get('has_more', 0)
                
                logger.info(f'请求完成，old_cursor: {old_cursor}, new_cursor: {self.cursor}, has_more: {not self.finished}')

                if aweme_list := data.get('aweme_list', []):
                    logger.info(f'API返回 {len(aweme_list)} 个作品')
                    
                    # 保留原始顺序，只筛选符合日期范围的作品
                    filtered_aweme_list = []
                    all_before_earliest = True
                    
                    for item in aweme_list:
                        item_date = date.fromtimestamp(item['create_time'])
                        logger.debug(f'作品ID: {item.get("aweme_id")}, 日期: {item_date}')
                        
                        # 检查是否符合日期范围
                        date_match = True
                        if earliest_date:
                            date_match &= (item_date >= earliest_date)
                        if latest_date:
                            date_match &= (item_date <= latest_date)
                        
                        if date_match:
                            filtered_aweme_list.append(item)
                            all_before_earliest = False
                            logger.info(f'添加符合条件的作品: ID={item.get("aweme_id")}, 日期={item_date}')
                        
                        # 即使不符合日期范围，也要检查是否所有作品都早于最早日期
                        elif earliest_date and item_date >= earliest_date:
                            all_before_earliest = False
                    
                    items.extend(filtered_aweme_list)
                    logger.info(f'本次筛选后添加 {len(filtered_aweme_list)} 个作品，累计 {len(items)} 个符合条件的作品')
                    
                    # 检查是否需要停止获取
                    if earliest_date and all_before_earliest:
                        logger.info(f'已获取到所有符合条件的作品，停止获取')
                        self.finished = True
                    
                    # 检查 cursor 是否更新
                    if self.cursor == old_cursor and request_count > 1:
                        logger.warning(f'Cursor 没有更新，可能已经获取到所有作品，停止获取')
                        self.finished = True

                Acquire._wait()
            
            logger.success(f'共获取到 {len(items)} 个作品')
            
            # 保存缓存
            cache_key = self._get_cache_key(sec_user_id, earliest_date, latest_date)
            self._save_cache(cache_key, items)
            logger.info(f"已缓存 {len(items)} 个作品")
            
            return items
        except Exception as e:
            logger.error(f"获取作品列表失败: {str(e)}")
            return None
