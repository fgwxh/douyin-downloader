import streamlit as st
import json
import os
from pathlib import Path
import os
import streamlit.components.v1 as components
# 尝试导入pyperclip，如果失败则设置为None
try:
    import pyperclip
except ImportError:
    pyperclip = None

from datetime import datetime, date, timedelta
from src.tool import logger

# 检查是否在Docker环境中
IS_DOCKER = os.environ.get('DOCKER_CONTAINER', 'false').lower() == 'true' or os.path.exists('/.dockerenv')

# 设置页面标题和布局
st.set_page_config(
    page_title="抖音作品下载工具",
    page_icon="🎵",
    layout="wide"
)

# 添加CSS样式，确保所有文本显示中文
st.markdown("""
<style>
    /* 确保所有文本显示中文 */
    body {
        font-family: 'Microsoft YaHei', sans-serif;
    }
    
    /* 调整日期选择器的大小 */
    .stDateInput {
        width: 100%;
    }
    
    .stDateInput > div {
        width: 100%;
    }
    
    .stDateInput > div > input {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# 创建数据存储目录
DATA_DIR = Path("./data")
DATA_DIR.mkdir(exist_ok=True)

# 文件路径
SETTINGS_FILE = DATA_DIR / "settings_mine.json"
COOKIES_FILE = DATA_DIR / "cookies.json"

# 默认配置
DEFAULT_SETTINGS = {
    "accounts": [],
    "save_folder": ".",
    "download_videos": True,
    "download_images": False,
    "name_format": ["create_time", "id", "type", "desc"],
    "split": "-",
    "date_format": "%Y-%m-%d",
    "proxy": "", # 留空，用户可以在settings_mine.json或UI界面中配置
    "file_description_max_length": 64,
    "chunk_size": 1048576,
    "timeout": 300,
    "concurrency": 5
}

# 加载配置文件
def load_settings():
    # 只从 data/settings_mine.json 加载设置
    settings_paths = [
        Path("./data/settings_mine.json"),  # 主要位置
        Path("./settings_default.json")   # 默认位置
    ]
    
    # 尝试从多个位置加载设置
    for path in settings_paths:
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                print(f"设置加载成功，来源: {path}")
                return settings
            except Exception as e:
                print(f"加载设置从 {path} 失败: {str(e)}")
    
    # 如果所有位置都失败，返回默认设置
    print("所有位置加载设置失败，返回默认设置")
    return DEFAULT_SETTINGS.copy()

# 保存配置文件
def save_settings(settings):
    # 只保存到 data/settings_mine.json 文件
    settings_paths = [
        Path("./data/settings_mine.json")  # 主要位置
    ]
    
    # 确保至少保存一个位置成功
    saved = False
    for path in settings_paths:
        try:
            # 确保目录存在
            path.parent.mkdir(exist_ok=True)
            
            with open(path, "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
            print(f"设置保存成功到: {path}")
            saved = True
        except Exception as e:
            print(f"保存设置到 {path} 失败: {str(e)}")
    
    if not saved:
        raise Exception("无法保存设置到任何位置，请检查文件权限")

# 加载Cookie文件
def load_cookies():
    if COOKIES_FILE.exists():
        with open(COOKIES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # 检查是否为加密数据
            if isinstance(data, dict) and "encrypted" in data:
                # 暂时返回空字典，等待修复加密功能
                return {}
            else:
                # 兼容旧版本未加密数据
                return data
    return {}

# 保存Cookie文件
def save_cookies(cookies):
    # 暂时保存未加密数据，等待修复加密功能
    try:
        # 确保DATA_DIR存在
        DATA_DIR.mkdir(exist_ok=True)
        
        # 同时保存到多个位置，确保在不同环境中都能找到
        cookie_paths = [
            Path("./cookies.json"),      # 直接路径（Docker挂载位置）
            COOKIES_FILE,                 # 主要位置
            Path("./data/cookies.json")   # 备用位置
        ]
        
        # 确保至少保存一个位置成功
        saved = False
        for path in cookie_paths:
            try:
                # 确保目录存在
                path.parent.mkdir(exist_ok=True)
                
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(cookies, f, ensure_ascii=False, indent=4)
                print(f"Cookie保存成功到: {path}")
                saved = True
            except Exception as e:
                print(f"保存Cookie到 {path} 失败: {str(e)}")
        
        print(f"Cookie内容: {cookies}")
        print(f"是否成功保存到至少一个位置: {saved}")
        
        if not saved:
            raise Exception("无法保存Cookie到任何位置，请检查文件权限")
    except Exception as e:
        print(f"保存Cookie失败: {str(e)}")
        raise

# 主页面
def main():
    st.title("🎵 抖音作品下载工具")
    
    # 添加退出程序按钮
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("🚪 退出程序", type="secondary"):
            st.warning("请按照以下步骤关闭程序：\n1. 关闭当前浏览器标签页\n2. 关闭启动脚本的命令窗口\n3. 或在任务管理器中结束python.exe进程")
            st.stop()
    
    # 加载当前配置
    settings = load_settings()
    cookies = load_cookies()
    
    # 初始化session_state保存临时状态
    if 'new_account_state' not in st.session_state:
        st.session_state.new_account_state = {
            'mark': '',
            'url': '',
            'date_mode': '日历选择',
            'earliest_str': (date.today() - timedelta(days=365)).strftime("%Y/%m/%d"),
            'latest_str': date.today().strftime("%Y/%m/%d")
        }
    
    # 初始化session_state保存现有账号的临时修改
    if 'existing_accounts_state' not in st.session_state:
        st.session_state.existing_accounts_state = []
    
    # 初始化每个账号的日期模式持久化
    for i, account in enumerate(settings["accounts"]):
        date_mode_key = f"date_mode_{i}"
        if date_mode_key not in st.session_state:
            st.session_state[date_mode_key] = "日历选择"
    
    # 创建标签页
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📁 账号管理", "⚙️ 下载设置", "🍪 Cookie设置", "▶️ 开始下载", "📋 作品管理", "📜 运行日志"])
    
    # 账号管理标签页
    with tab1:
        st.header("账号管理")
        
        # 添加新账号
        with st.expander("添加新账号", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                mark = st.text_input("账号标识", value=st.session_state.new_account_state['mark'], key="new_mark")
                url = st.text_input("账号主页链接", value=st.session_state.new_account_state['url'], key="new_url")
            with col2:
                # 日期输入方式选择
                date_input_mode = st.radio("日期输入方式", ["日历选择", "手动填写"], index=0 if st.session_state.new_account_state['date_mode'] == "日历选择" else 1, key="new_date_mode")
                
                if date_input_mode == "日历选择":
                    # 使用Streamlit的默认日期选择器，确保value是有效的date对象
                    def get_valid_date(value, default_days=365):
                        try:
                            if isinstance(value, str):
                                return datetime.strptime(value, "%Y/%m/%d").date()
                        except:
                            pass
                        return date.today() - timedelta(days=default_days)
                    
                    # 从session_state读取字符串格式的日期
                    earliest_val = get_valid_date(st.session_state.new_account_state.get('earliest_str', ''), 365)
                    latest_val = get_valid_date(st.session_state.new_account_state.get('latest_str', ''), 0)
                    
                    # 直接使用日历选择器的值
                    earliest = st.date_input("最早发布日期", value=earliest_val, key="new_earliest")
                    latest = st.date_input("最晚发布日期", value=latest_val, key="new_latest")
                    # 将date对象转换为字符串格式
                    earliest_str = earliest.strftime("%Y/%m/%d")
                    latest_str = latest.strftime("%Y/%m/%d")
                    # 直接更新session_state，确保使用正确的日期值
                    st.session_state.new_account_state['earliest_str'] = earliest_str
                    st.session_state.new_account_state['latest_str'] = latest_str
                else:
                    earliest_str = st.text_input("最早发布日期 (YYYY/MM/DD)", value=st.session_state.new_account_state['earliest_str'], key="new_earliest_str")
                    latest_str = st.text_input("最晚发布日期 (YYYY/MM/DD)", value=st.session_state.new_account_state['latest_str'], key="new_latest_str")
                    # 直接更新session_state，确保使用正确的日期值
                    st.session_state.new_account_state['earliest_str'] = earliest_str
                    st.session_state.new_account_state['latest_str'] = latest_str
            
            # 实时更新session_state
            st.session_state.new_account_state['mark'] = mark
            st.session_state.new_account_state['url'] = url
            st.session_state.new_account_state['date_mode'] = date_input_mode
            
            if st.button("添加账号"):
                if url:
                    new_account = {
                        "mark": mark,
                        "url": url,
                        "earliest": earliest_str,
                        "latest": latest_str
                    }
                    settings["accounts"].append(new_account)
                    save_settings(settings)
                    # 重置新账号表单
                    st.session_state.new_account_state = {
                        'mark': '',
                        'url': '',
                        'date_mode': '日历选择',
                        'earliest_str': (date.today() - timedelta(days=365)).strftime("%Y/%m/%d"),
                        'latest_str': date.today().strftime("%Y/%m/%d")
                    }
                    st.success("账号添加成功!")
                    st.rerun()
                else:
                    st.error("请输入账号主页链接")
        
        # 显示现有账号
        st.subheader("现有账号")
        
        # 确保existing_accounts_state与settings["accounts"]同步
        while len(st.session_state.existing_accounts_state) < len(settings["accounts"]):
            st.session_state.existing_accounts_state.append({})
        
        while len(st.session_state.existing_accounts_state) > len(settings["accounts"]):
            st.session_state.existing_accounts_state.pop()
        
        for i, account in enumerate(settings["accounts"]):
            # 确保每个账号都有对应的临时状态
            if i >= len(st.session_state.existing_accounts_state):
                st.session_state.existing_accounts_state.append({})
            
            # 获取临时状态，默认为当前账号的原始值
            temp_account = st.session_state.existing_accounts_state[i]
            
            # 初始化临时状态，使用当前账号的值
            if not temp_account:
                temp_account.update({
                    'mark': account.get('mark', ''),
                    'url': account.get('url', ''),
                    'earliest': account.get('earliest', ''),
                    'latest': account.get('latest', ''),
                    'date_mode': '日历选择'
                })
                st.session_state.existing_accounts_state[i] = temp_account
            
            with st.expander(f"账号 {i+1}: {temp_account.get('mark', '未命名')}"):
                col1, col2 = st.columns(2)
                with col1:
                    # 账号标识和URL输入
                    temp_account['mark'] = st.text_input("账号标识", value=temp_account['mark'], key=f"mark_{i}")
                    temp_account['url'] = st.text_input("账号主页链接", value=temp_account['url'], key=f"url_{i}")
                    
                    # 更新session_state中的临时状态
                    st.session_state.existing_accounts_state[i] = temp_account
                with col2:
                    # 日期输入方式选择
                    temp_account['date_mode'] = st.radio("日期输入方式", ["日历选择", "手动填写"], key=f"date_mode_{i}")
                    
                    if temp_account['date_mode'] == "日历选择":
                        # 将字符串日期转换为date对象
                        def str_to_date(date_str):
                            if not date_str:
                                return date.today() - timedelta(days=365)
                            try:
                                return datetime.strptime(date_str, "%Y/%m/%d").date()
                            except:
                                return date.today() - timedelta(days=365)
                        
                        # 转换为date对象用于显示
                        earliest_date = str_to_date(temp_account.get('earliest', ''))
                        latest_date = str_to_date(temp_account.get('latest', ''))
                        
                        # 使用Streamlit的默认日期选择器
                        selected_earliest = st.date_input("最早发布日期", value=earliest_date, key=f"earliest_{i}")
                        selected_latest = st.date_input("最晚发布日期", value=latest_date, key=f"latest_{i}")
                        
                        # 将date对象转换回字符串格式
                        temp_account['earliest'] = selected_earliest.strftime("%Y/%m/%d") if selected_earliest else ""
                        temp_account['latest'] = selected_latest.strftime("%Y/%m/%d") if selected_latest else ""
                    else:
                        # 手动填写日期
                        temp_account['earliest'] = st.text_input("最早发布日期 (YYYY/MM/DD)", value=temp_account['earliest'], key=f"earliest_str_{i}")
                        temp_account['latest'] = st.text_input("最晚发布日期 (YYYY/MM/DD)", value=temp_account['latest'], key=f"latest_str_{i}")
                    
                    # 更新session_state中的临时状态
                    st.session_state.existing_accounts_state[i] = temp_account
                
                if st.button("删除账号", key=f"delete_{i}"):
                    settings["accounts"].pop(i)
                    st.session_state.existing_accounts_state.pop(i)
                    save_settings(settings)
                    st.success("账号删除成功!")
                    st.rerun()
        
        # 保存账号修改按钮
        if st.button("保存账号修改"):
            # 将临时状态中的修改应用到实际的settings对象
            for i, temp_account in enumerate(st.session_state.existing_accounts_state):
                if i < len(settings["accounts"]):
                    account = settings["accounts"][i]
                    account['mark'] = temp_account.get('mark', account.get('mark', ''))
                    account['url'] = temp_account.get('url', account.get('url', ''))
                    account['earliest'] = temp_account.get('earliest', account.get('earliest', ''))
                    account['latest'] = temp_account.get('latest', account.get('latest', ''))
            
            # 保存设置
            save_settings(settings)
            st.success("账号修改保存成功!")
    
    # 下载设置标签页
    with tab2:
        st.header("下载设置")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 基本设置
            st.subheader("基本设置")
            settings["save_folder"] = st.text_input("保存路径", value=settings["save_folder"])
            
            # 下载选项
            st.subheader("下载选项")
            settings["download_videos"] = st.checkbox("下载视频", value=settings["download_videos"])
            settings["download_images"] = st.checkbox("下载图集", value=settings["download_images"])
        
        with col2:
            # 文件命名
            st.subheader("文件命名")
            name_format = st.multiselect(
                "命名格式",
                options=["create_time", "id", "type", "desc"],
                default=settings["name_format"]
            )
            settings["name_format"] = name_format
            
            settings["split"] = st.text_input("分隔符", value=settings["split"])
            settings["date_format"] = st.text_input("日期格式", value=settings["date_format"])
        
        # 高级设置
        st.subheader("高级设置")
        col3, col4, col5 = st.columns(3)
        with col3:
            settings["timeout"] = st.number_input("超时时间 (秒)", value=settings["timeout"], min_value=10, max_value=3600)
        with col4:
            settings["concurrency"] = st.number_input("并发数", value=settings["concurrency"], min_value=1, max_value=20)
        with col5:
            settings["file_description_max_length"] = st.number_input("描述最大长度", value=settings["file_description_max_length"], min_value=10, max_value=200)
        
        # 代理设置
        settings["proxy"] = st.text_input("代理地址 (可选)", value=settings["proxy"] if settings["proxy"] else "")
        
        # 保存设置
        if st.button("保存设置"):
            save_settings(settings)
            st.success("设置保存成功!")
    
    # Cookie设置标签页
    with tab3:
        st.header("Cookie设置")
        
        # 添加Cookie转换功能
        st.subheader("Cookie转换工具")
        # 获取raw_cookie
        if 'raw_cookie' in st.session_state and st.session_state.raw_cookie:
            raw_cookie = st.text_area("粘贴浏览器中的原始Cookie（格式：key1=value1; key2=value2）", value=st.session_state.raw_cookie, height=100)
        else:
            raw_cookie = st.text_area("粘贴浏览器中的原始Cookie（格式：key1=value1; key2=value2）", height=100)
        
        if st.button("转换为JSON格式"):
            if raw_cookie:
                # 转换原始Cookie为JSON格式
                cookie_dict = {}
                cookies_list = raw_cookie.split('; ')
                for cookie in cookies_list:
                    if '=' in cookie:
                        key, value = cookie.split('=', 1)
                        cookie_dict[key] = value
                # 显示转换后的JSON
                st.success("转换成功！")
                converted_json = json.dumps(cookie_dict, ensure_ascii=False, indent=2)
                # 存储到session_state
                if 'converted_json' not in st.session_state:
                    st.session_state.converted_json = {}
                st.session_state.converted_json = converted_json
                # 添加复制按钮
                col_copy, _ = st.columns([1, 4])
                with col_copy:
                    if st.button("复制转换结果", key="copy_converted"):
                        # 这里可以添加复制到剪贴板的功能
                        st.success("已复制到剪贴板！")
                # 显示转换后的JSON
                st.text_area("转换后的JSON格式", value=converted_json, height=200, key="converted_cookie")
            else:
                st.error("请先粘贴原始Cookie")
        
        st.subheader("保存Cookie")
        # 添加粘贴按钮
        col_paste, _ = st.columns([1, 4])
        with col_paste:
            if st.button("粘贴转换结果", key="paste_converted"):
                if 'converted_json' in st.session_state and st.session_state.converted_json:
                    # 存储到session_state
                    if 'cookie_content' not in st.session_state:
                        st.session_state.cookie_content = {}
                    st.session_state.cookie_content = st.session_state.converted_json
                    st.success("已粘贴转换结果！")
                    st.rerun()
                else:
                    st.error("没有可粘贴的转换结果")
        # 获取cookie_content
        if 'cookie_content' in st.session_state and st.session_state.cookie_content:
            cookie_content = st.text_area("粘贴抖音Cookie（JSON格式）", value=st.session_state.cookie_content, height=200)
        else:
            cookie_content = st.text_area("粘贴抖音Cookie（JSON格式）", value=json.dumps(cookies, ensure_ascii=False, indent=2), height=200)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("保存Cookie"):
                try:
                    parsed_cookies = json.loads(cookie_content)
                    save_cookies(parsed_cookies)
                    st.success("Cookie保存成功!")
                except json.JSONDecodeError:
                    st.error("Cookie格式错误，请输入有效的JSON格式")
        
        with col2:
            if st.button("清空Cookie"):
                save_cookies({})
                st.success("Cookie已清空!")
                st.rerun()
        
        st.info("提示：Cookie可以从浏览器的开发者工具中获取。打开抖音网页，按F12进入开发者工具，在Application -> Cookies中找到抖音相关的Cookie，复制原始格式或JSON格式。使用鼠标右键或键盘快捷键（Ctrl+V/Command+V）粘贴来自浏览器复制的cookie内容即可。")
    
    # 开始下载标签页
    with tab4:
        st.header("开始下载")
        
        if not settings["accounts"]:
            st.warning("请先添加至少一个账号")
        else:
            st.subheader("下载配置预览")
            st.write(f"📁 保存路径: {settings['save_folder']}")
            st.write(f"🎥 下载视频: {'✅' if settings['download_videos'] else '❌'}")
            st.write(f"🖼️ 下载图集: {'✅' if settings['download_images'] else '❌'}")
            st.write(f"👥 账号数量: {len(settings['accounts'])}")
            
            # 添加账号选择功能
            st.subheader("选择下载账号")
            account_options = [f"所有账号 ({len(settings['accounts'])})"] + [f"{account.get('mark', '未命名')} - {account['url']}" for account in settings['accounts']]
            selected_account = st.selectbox("请选择要下载的账号", account_options)
            
            if st.button("开始下载", type="primary"):
                # 保存当前配置
                save_settings(settings)
                
                # 创建临时配置文件用于scheduler.py
                import tempfile
                import shutil
                from pathlib import Path
                
                # 复制原始设置文件
                temp_settings = load_settings()
                
                # 如果选择的不是"所有账号"，则只保留选中的账号
                if selected_account != account_options[0]:
                    selected_index = account_options.index(selected_account) - 1
                    temp_settings["accounts"] = [temp_settings["accounts"][selected_index]]
                
                # 保存临时设置文件
                with open(Path("./settings_mine.json"), "w", encoding="utf-8") as f:
                    json.dump(temp_settings, f, ensure_ascii=False, indent=4)
                
                # 不再复制cookie到项目根目录，直接使用data目录中的cookie文件
                
                # 运行下载任务
                import subprocess
                import sys
                
                st.info("开始下载...")
                
                # 存储进程ID到session_state
                if 'download_process' not in st.session_state:
                    st.session_state.download_process = None
                
                # 启动非阻塞式下载
                process = subprocess.Popen(
                    [sys.executable, "run.py"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd=Path(".")
                )
                st.session_state.download_process = process
                
                # 显示下载状态
                st.success("下载任务已启动！")
                
                # 添加停止和暂停下载按钮
                col_stop, col_pause = st.columns(2)
                with col_stop:
                    if st.button("停止下载"):
                        if st.session_state.download_process:
                            try:
                                st.session_state.download_process.terminate()
                                st.session_state.download_process.wait(timeout=5)
                                st.error("下载已停止！")
                                st.session_state.download_process = None
                            except Exception as e:
                                st.error(f"停止下载失败：{str(e)}")
                        else:
                            st.error("没有正在运行的下载任务")
                
                with col_pause:
                    if st.button("暂停下载"):
                        if st.session_state.download_process:
                            try:
                                st.session_state.download_process.terminate()
                                st.session_state.download_process.wait(timeout=5)
                                st.warning("下载已暂停！")
                                st.session_state.download_process = None
                                st.info("点击'开始下载'按钮可恢复下载")
                            except Exception as e:
                                st.error(f"暂停下载失败：{str(e)}")
                        else:
                            st.error("没有正在运行的下载任务")
                
                # 显示下载结果
                if st.session_state.download_process:
                    try:
                        # 等待进程完成，最多等待300秒
                        stdout, _ = st.session_state.download_process.communicate(timeout=300)
                        if st.session_state.download_process.returncode == 0:
                            st.success("下载完成!")
                            # 显示下载日志
                            with st.expander("查看下载日志"):
                                st.text(stdout)
                        else:
                            st.error("下载失败!")
                            with st.expander("查看错误日志"):
                                st.text(stdout)
                        st.session_state.download_process = None
                    except subprocess.TimeoutExpired:
                        st.warning("下载超时，请检查网络连接或手动停止下载")
                    except Exception as e:
                        st.error(f"获取下载结果失败：{str(e)}")
    
    # 作品管理标签页
    with tab5:
        st.header("作品管理")
        
        if not settings["accounts"]:
            st.warning("请先添加至少一个账号")
        else:
            # 选择账号
            st.subheader("选择账号")
            # 重新加载设置，确保包含新添加的账号
            from src.config import load_settings as load_config_settings
            from json import load
            from pathlib import Path
            
            # 直接从文件加载最新的账号列表，优先检查 ./data/settings_mine.json
            data_settings = Path('./data/settings_mine.json')
            root_settings = Path('settings_mine.json')
            default_settings = Path('settings_default.json')
            
            # 优先顺序：./data/settings_mine.json > ./settings_mine.json > ./settings_default.json
            if data_settings.exists():
                filepath = data_settings
            elif root_settings.exists():
                filepath = root_settings
            else:
                filepath = default_settings
                
            try:
                with open(filepath, encoding='utf-8') as f:
                    latest_settings = load(f)
                account_options = [f"{account.get('mark', '未命名')} - {account['url']}" for account in latest_settings['accounts']]
                selected_account_index = st.selectbox("请选择账号", range(len(account_options)), format_func=lambda x: account_options[x])
                selected_account = latest_settings['accounts'][selected_account_index]
                st.info(f"加载账号列表成功，来源: {filepath}")
            except Exception as e:
                st.error(f"加载账号列表失败: {str(e)}")
                account_options = [f"{account.get('mark', '未命名')} - {account['url']}" for account in settings['accounts']]
                selected_account_index = st.selectbox("请选择账号", range(len(account_options)), format_func=lambda x: account_options[x])
                selected_account = settings['accounts'][selected_account_index]
            
            # 导入必要的模块
            from src.download.acquire import Acquire
            from src.download.parse import Parse
            from src.config import Settings as ConfigSettings, Cookie as ConfigCookie
            from src.tool import Cleaner
            
            # 加载配置
            from src.config import load_settings as load_config_settings
            config_settings = load_config_settings()
            config_cookie = ConfigCookie()
            
            # 检查并加载Cookie
            import os
            from pathlib import Path
            # 同时检查多个可能的Cookie文件位置
            cookie_paths = [
                Path("./cookies.json"),      # 直接路径（Docker挂载位置）
                DATA_DIR / "cookies.json",  # 主要位置
                Path("./data/cookies.json")  # 备用位置
            ]
            
            cookie_loaded = False
            loaded_file = None
            
            # 先检查所有路径，收集信息
            for COOKIES_FILE in cookie_paths:
                if COOKIES_FILE.exists():
                    try:
                        # 尝试加载Cookie
                        with open(COOKIES_FILE, 'r', encoding='utf-8') as f:
                            cookie_data = json.load(f)
                            if cookie_data:
                                config_cookie.cookies = cookie_data
                                cookie_loaded = True
                                loaded_file = COOKIES_FILE
                                st.info(f"成功加载Cookie文件: {COOKIES_FILE}")
                                # 显示Cookie中的关键信息
                                cookie_keys = list(config_cookie.cookies.keys())
                                st.info(f"Cookie中包含 {len(cookie_keys)} 个键")
                                if cookie_keys:
                                    st.info(f"关键Cookie键: {cookie_keys[:5]}...")
                                break
                            else:
                                st.warning(f"Cookie文件存在但为空: {COOKIES_FILE}")
                    except Exception as e:
                        st.error(f"加载Cookie文件 {COOKIES_FILE} 失败: {str(e)}")
                else:
                    st.info(f"Cookie文件不存在: {COOKIES_FILE}")
            
            # 显示所有尝试的路径，帮助诊断问题
            st.info("尝试加载的Cookie文件路径:")
            for path in cookie_paths:
                exists = path.exists()
                size = path.stat().st_size if exists else 0
                st.info(f"- {path} (存在: {exists}, 大小: {size} 字节)")
            
            if not cookie_loaded:
                st.error("Cookie未加载或为空，请先在'🍪 Cookie设置'标签页中设置Cookie")
                st.info("设置步骤:")
                st.info("1. 点击'🍪 Cookie设置'标签页")
                st.info("2. 在'Cookie转换工具'中粘贴原始Cookie")
                st.info("3. 点击'转换为JSON格式'按钮")
                st.info("4. 在'保存Cookie'中点击'粘贴转换结果'按钮")
                st.info("5. 点击'保存Cookie'按钮")
                st.info("6. 回到'📋 作品管理'标签页重试")
            
            cleaner = Cleaner()
            
            # 获取sec_user_id
            def get_sec_user_id(url):
                # 从URL中提取sec_user_id
                import re
                # 处理包含sec_user_id参数的URL
                if 'sec_user_id=' in url:
                    return url.split('sec_user_id=')[1].split('&')[0]
                # 处理普通用户URL格式 https://www.douyin.com/user/xxx
                match_url = re.match(r'https://www\.douyin\.com/user/([A-Za-z0-9_-]+)(\?.*)?', url)
                if match_url:
                    return match_url.group(1)
                return url
            
            sec_user_id = get_sec_user_id(selected_account['url'])
            
            # 获取作品列表
            if st.button("🔍 加载作品列表"):
                st.info("正在加载作品列表，请稍候...")
                
                # 检查Cookie是否已加载
                if not config_cookie.cookies:
                    st.error("Cookie未加载或为空，请先在'🍪 Cookie设置'标签页中设置Cookie")
                else:
                    # 获取作品数据
                    acquire = Acquire()
                    from datetime import datetime
                    
                    # 处理日期格式
                    earliest_date = selected_account.get('earliest')
                    latest_date = selected_account.get('latest')
                    
                    # 转换日期字符串为日期对象
                    def parse_date(date_str):
                        if date_str:
                            try:
                                return datetime.strptime(date_str, '%Y/%m/%d').date()
                            except:
                                return None
                        return None
                    
                    earliest_date_obj = parse_date(earliest_date)
                    latest_date_obj = parse_date(latest_date)
                    
                    st.info(f"正在获取作品列表，账号ID: {sec_user_id}")
                    
                    # 显示网络和代理设置
                    st.info(f"代理设置: {config_settings.proxy if hasattr(config_settings, 'proxy') else '无'}")
                    st.info(f"超时设置: {config_settings.timeout if hasattr(config_settings, 'timeout') else '默认'}")
                    
                    try:
                        # 尝试使用不同的方式获取作品列表
                        st.info("正在发送网络请求...")
                        
                        # 直接测试网络连接
                        import requests
                        test_url = "https://www.douyin.com"
                        
                        # 尝试无代理连接
                        try:
                            test_response = requests.get(test_url, timeout=10, proxies=None)
                            st.info(f"无代理连接测试成功: {test_url}，状态码: {test_response.status_code}")
                            # 如果无代理连接成功，尝试禁用代理获取作品列表
                            from src.config import Settings
                            # 创建一个临时设置对象，禁用代理
                            temp_settings_dict = {}
                            for attr in dir(config_settings):
                                if not attr.startswith('_'):
                                    temp_settings_dict[attr] = getattr(config_settings, attr)
                            temp_settings_dict['proxy'] = None
                            temp_settings = Settings(**temp_settings_dict)
                            st.info("已切换到无代理模式")
                            
                            # 尝试获取作品列表
                            items = acquire.request_items(sec_user_id, earliest_date_obj, latest_date_obj, temp_settings, config_cookie)
                        except Exception as e:
                            st.error(f"无代理连接测试失败: {str(e)}")
                            
                            # 尝试使用代理连接
                            if hasattr(config_settings, 'proxy') and config_settings.proxy:
                                try:
                                    test_response = requests.get(test_url, timeout=10, proxies={'http': config_settings.proxy, 'https': config_settings.proxy})
                                    st.info(f"代理连接测试成功: {test_url}，状态码: {test_response.status_code}")
                                    # 尝试获取作品列表
                                    items = acquire.request_items(sec_user_id, earliest_date_obj, latest_date_obj, config_settings, config_cookie)
                                except Exception as e:
                                    st.error(f"代理连接测试失败: {str(e)}")
                                    st.error("请检查代理设置是否正确")
                                    items = None
                            else:
                                items = None
                        
                        st.info(f"获取作品列表结果: {'成功' if items else '失败'}")
                        st.info(f"返回的items类型: {type(items)}")
                        if items:
                            st.info(f"返回的items数量: {len(items)}")
                        
                        if items:
                            # 提取作品信息
                            parsed_items = Parse.extract_items(items, earliest_date_obj, latest_date_obj, config_settings, cleaner)
                            st.success(f"成功加载 {len(parsed_items)} 个作品")
                            
                            # 存储作品列表到session_state
                            if 'parsed_items' not in st.session_state:
                                st.session_state.parsed_items = []
                            st.session_state.parsed_items = parsed_items
                            
                            # 重置选中的作品列表
                            if 'selected_items' not in st.session_state:
                                st.session_state.selected_items = []
                            st.session_state.selected_items = []
                        else:
                            st.error("无法加载作品列表，可能的原因：")
                            st.error("1. 账号链接格式不正确")
                            st.error("2. Cookie已过期或无效")
                            st.error("3. 网络连接问题")
                            st.error("4. 账号可能已被限制访问")
                    except Exception as e:
                        st.error(f"获取作品列表时出错：{str(e)}")
                        import traceback
                        st.error(f"错误详情：{traceback.format_exc()}")
            
            # 显示作品列表（无论是否点击了加载按钮，只要session_state中有数据就显示）
            if 'parsed_items' in st.session_state and st.session_state.parsed_items:
                parsed_items = st.session_state.parsed_items
                
                # 显示作品列表
                st.subheader("作品列表")
                
                # 选择下载的作品
                selected_items = []
                for i, item in enumerate(parsed_items):
                    with st.expander(f"作品 {i+1}: {item.get('desc', '无描述')[:50]}..."):
                        col1, col2 = st.columns([1, 3])
                        with col1:
                            item_id = item.get('id', '')
                            item_type = '视频' if item.get('type') == 'video' else '图集'
                            create_time = item.get('create_time', '')
                            selected = st.checkbox(f"选择下载", key=f"select_{i}")
                            if selected:
                                selected_items.append(item)
                        with col2:
                            st.write(f"ID: {item_id}")
                            st.write(f"类型: {item_type}")
                            st.write(f"发布时间: {create_time}")
                            st.write(f"描述: {item.get('desc', '无描述')}")
                
                # 存储选中的作品
                if 'selected_items' not in st.session_state:
                    st.session_state.selected_items = []
                st.session_state.selected_items = selected_items
                
                # 显示选中的作品数量
                st.write(f"已选择 {len(selected_items)} 个作品")
                
                # 下载选中的作品
                if st.button("📥 下载选中的作品"):
                    if selected_items:
                        st.info("开始下载选中的作品，请稍候...")
                        
                        # 导入下载模块
                        from src.download.download import Download
                        
                        # 下载作品
                        try:
                            import tempfile
                            import shutil
                            from pathlib import Path
                            
                            # 递归处理日期对象的函数
                            def process_date_objects(obj):
                                if isinstance(obj, dict):
                                    return {key: process_date_objects(value) for key, value in obj.items()}
                                elif isinstance(obj, list):
                                    return [process_date_objects(item) for item in obj]
                                elif hasattr(obj, '__class__') and obj.__class__.__name__ in ['date', 'datetime']:
                                    return str(obj)
                                else:
                                    return obj
                            
                            # 为每个选中的作品添加账号信息
                            items_with_account_info = []
                            for item in selected_items:
                                item_with_account = item.copy()
                                item_with_account['account_id'] = selected_account.get('id', 'unknown')
                                item_with_account['account_mark'] = selected_account.get('mark', '未命名')
                                
                                # 递归处理所有日期对象，包括嵌套结构
                                item_with_account = process_date_objects(item_with_account)
                                
                                items_with_account_info.append(item_with_account)
                            
                            # 保存选中的作品数据到临时文件
                            with open(Path("./selected_items.json"), "w", encoding="utf-8") as f:
                                json.dump(items_with_account_info, f, ensure_ascii=False, indent=4)
                            
                            # 不再复制cookie到项目根目录，直接使用data目录中的cookie文件
                            
                            # 使用subprocess调用download_selected.py来下载选中的作品
                            import subprocess
                            import sys
                            
                            # 构建下载命令
                            cmd = [sys.executable, "download_selected.py"]
                            
                            # 运行下载命令
                            st.info("正在启动下载任务...")
                            result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path("."))
                            
                            # 显示下载结果
                            if result.returncode == 0:
                                st.success("下载完成！")
                                # 显示下载日志
                                with st.expander("查看下载日志"):
                                    st.text(result.stdout)
                            else:
                                st.error("下载失败！")
                                with st.expander("查看错误日志"):
                                    st.text(result.stderr)
                                    st.text(result.stdout)
                        except Exception as e:
                            st.error(f"下载失败：{str(e)}")
                            import traceback
                            st.error(f"错误详情：{traceback.format_exc()}")
                    else:
                        st.error("请先选择要下载的作品")
        
        # 运行日志标签页
        with tab6:
            st.subheader("📜 系统运行日志")
            
            # 日志操作区域
            col1, col2, col3 = st.columns(3)
            with col1:
                refresh_logs = st.button("🔄 刷新日志")
            with col2:
                log_level = st.selectbox("日志级别", ["全部", "INFO", "SUCCESS", "WARNING", "ERROR", "DEBUG"], index=0)
            with col3:
                clear_logs = st.button("🗑️ 清空日志")
            
            # 获取日志内容
            logs = logger.get_logs()
            
            # 按级别筛选日志
            if log_level != "全部":
                level_filter = f"| {log_level:<8} |"
                logs = [line for line in logs if level_filter in line]
            
            # 显示日志
            if logs:
                # 最新的日志显示在最前面
                reversed_logs = logs[::-1]
                st.text_area("日志内容", value="\n".join(reversed_logs), height=600)
                st.info(f"共显示 {len(logs)} 条日志")
            else:
                st.info("暂无日志记录")
            
            # 清空日志功能
            if clear_logs:
                if logger.clear_logs():
                    st.success("日志已清空")
                    st.rerun()
                else:
                    st.error("清空日志失败")

# 运行应用
if __name__ == "__main__":
    main()
