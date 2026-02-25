from datetime import date
import time

from ..tool import Cleaner
from ..config import Settings, Account


class Parse:
    @staticmethod
    def _extract_value(data: dict, attribute_chain: str):
        '''根据 attribute_chain 从 dict 中提取值'''
        attributes = attribute_chain.split('.')
        for attribute in attributes:
            if '[' in attribute:
                parts = attribute.split('[', 1)
                attribute = parts[0]
                index = int(parts[1].split(']', 1)[0])
                data = data[attribute][index]
            else:
                data = data[attribute]
            if not data:
                return
        return data

    @staticmethod
    def extract_account(account: Account, item: dict, cleaner: Cleaner):
        '''提取账号 id、昵称，检查账号 mark'''
        account.id = Parse._extract_value(item, 'author.uid')
        account.name = cleaner.filter_name(
            Parse._extract_value(item, 'author.nickname'),
            default='无效账号昵称')
        account.mark = cleaner.filter_name(
            account.mark, default=account.name)

    @staticmethod
    def _extract_common(item: dict, result: dict, settings: Settings, cleaner: Cleaner):
        '''提取图文/视频作品共有信息'''
        result['id'] = Parse._extract_value(item, 'aweme_id')
        if desc:=Parse._extract_value(item, 'desc'):
            result['desc'] = cleaner.clear_spaces(cleaner.filter_name(desc))[:settings.file_description_max_length]
        else:
            result['desc'] = '作品描述为空'
        
        # 提取创建时间，添加错误处理
        create_timestamp = Parse._extract_value(item, 'create_time')
        if create_timestamp:
            try:
                result['create_timestamp'] = create_timestamp
                result['create_time_date'] = date.fromtimestamp(int(create_timestamp))
                result['create_time'] = date.strftime(result['create_time_date'], settings.date_format)
            except Exception:
                # 如果提取时间失败，使用当前时间
                result['create_timestamp'] = str(int(time.time()))
                result['create_time_date'] = date.today()
                result['create_time'] = date.strftime(result['create_time_date'], settings.date_format)
        else:
            # 如果没有创建时间，使用当前时间
            result['create_timestamp'] = str(int(time.time()))
            result['create_time_date'] = date.today()
            result['create_time'] = date.strftime(result['create_time_date'], settings.date_format)

    @staticmethod
    def _extract_gallery(gallery: dict, result: dict):
        '''提取图文作品信息'''
        result['type'] = '图集'
        result['share_url'] = f'https://www.douyin.com/note/{result["id"]}'
        result['downloads'] = []
        for image in gallery:
            url = Parse._extract_value(image, 'url_list[0]')
            width = Parse._extract_value(image, 'width')
            height = Parse._extract_value(image, 'height')
            result['downloads'].append((url, width, height))
        
        # 提取封面图URL，使用第一张图片作为封面
        if gallery:
            first_image = gallery[0]
            result['cover_url'] = Parse._extract_value(first_image, 'url_list[0]')
        else:
            result['cover_url'] = ''

    @staticmethod
    def _extract_video( video: dict, result: dict):
        '''提取视频作品信息'''
        result['type'] = '视频'
        # 强制使用.mp4扩展名，避免下载到.dash文件
        result['format'] = '.mp4'
        result['share_url'] = f'https://www.douyin.com/video/{result["id"]}'
        result['downloads'] = Parse._extract_value(
            video, 'play_addr.url_list[0]')
        result['height'] = Parse._extract_value(video, 'height')
        result['width'] = Parse._extract_value(video, 'width')
        
        # 提取封面图URL
        result['cover_url'] = Parse._extract_value(video, 'cover.url_list[0]')
        if not result['cover_url']:
            result['cover_url'] = ''

    @staticmethod
    def extract_items(items: list[dict], earliest: date, latest: date, settings: Settings, cleaner: Cleaner):
        '''提取发布作品信息并返回'''
        results = []
        from src.tool import logger
        
        logger.info(f'开始提取作品信息，共 {len(items)} 个作品')
        logger.info(f'日期过滤条件: 最早 {earliest}, 最晚 {latest}')
        logger.info(f'下载设置: 视频={settings.download_videos}, 图集={settings.download_images}')
        
        for i, item in enumerate(items):
            result = {}
            Parse._extract_common(item, result, settings, cleaner)
            
            # 检查日期过滤条件
            date_match = True
            if earliest:
                date_match &= (result['create_time_date'] >= earliest)
            if latest:
                date_match &= (result['create_time_date'] <= latest)
            
            logger.info(f'作品 {i+1}: ID={result.get("id")}, 日期={result.get("create_time_date")}, 日期匹配={date_match}')
            
            if date_match:
                if (gallery := Parse._extract_value(item, 'images')):
                    logger.info(f'作品 {i+1} 是图集，download_images={settings.download_images}')
                    if settings.download_images:
                        Parse._extract_gallery(gallery, result)
                        results.append(result)
                        logger.info(f'添加图集作品到结果列表')
                elif settings.download_videos:
                    video = Parse._extract_value(item, 'video')
                    if video:
                        logger.info(f'作品 {i+1} 是视频，添加到结果列表')
                        Parse._extract_video(video, result)
                        results.append(result)
                    else:
                        logger.info(f'作品 {i+1} 没有视频信息，跳过')
                else:
                    logger.info(f'作品 {i+1} 类型不匹配下载设置，跳过')
            else:
                logger.info(f'作品 {i+1} 日期不匹配，跳过')
        
        logger.info(f'提取完成，共 {len(results)} 个作品')
        return results
