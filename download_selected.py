from src.download.download import Download
from src.config import load_settings, Cookie
from src.tool import Cleaner
import json
import sys

if __name__ == '__main__':
    # 加载配置
    settings = load_settings()
    cookie = Cookie()
    cookie.load_cookies()
    cleaner = Cleaner()
    
    # 加载选中的作品数据
    try:
        with open('selected_items.json', 'r', encoding='utf-8') as f:
            selected_items = json.load(f)
        
        if not selected_items:
            print('没有选中的作品需要下载')
            sys.exit()
        
        # 下载选中的作品
        print(f'开始下载 {len(selected_items)} 个选中的作品...')
        
        # 获取账号信息
        account_id = selected_items[0].get('account_id', 'unknown')
        account_mark = selected_items[0].get('account_mark', '未命名')
        
        # 下载作品
        Download.download_items(selected_items, settings, cookie, cleaner)
        
        print('下载完成！')
    except FileNotFoundError:
        print('未找到选中的作品数据文件')
    except Exception as e:
        print(f'下载时发生错误: {str(e)}')
        import traceback
        traceback.print_exc()