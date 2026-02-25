// API基础URL - 使用相对路径，适应不同部署环境
const API_BASE_URL = '/api';

// 全局变量
let loadWorksAbortController = null;
let loadWorksProgressInterval = null;

// 页面加载完成后执行
window.addEventListener('DOMContentLoaded', async function() {
    // 初始化标签页切换
    initTabs();
    
    // 初始化表单事件
    initForms();
    
    // 初始化账号列表
    await loadAccounts();
    
    // 初始化设置
    await loadSettings();
    
    // 初始化Cookie
    await loadCookie();
    
    // 初始化配置管理
    await loadCurrentConfig();
    
    // 绑定配置管理事件监听器
    bindConfigEventListeners();
    
    // 初始化年份月份选择器
    initYearMonthSelectors();
});

// 初始化标签页切换
function initTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const tabId = this.getAttribute('data-tab');
            
            // 移除所有活动状态
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabPanes.forEach(pane => pane.classList.remove('active'));
            
            // 添加当前活动状态
            this.classList.add('active');
            document.getElementById(tabId).classList.add('active');
        });
    });
}

// 初始化年份月份选择器
function initYearMonthSelectors() {
    // 年份和月份选项已经在HTML中静态添加
    // 这里只需要确保默认选项正确
    const yearSelect = document.getElementById('works-year');
    const monthSelect = document.getElementById('works-month');
    
    if (yearSelect) {
        // 确保当前年份被选中
        const currentYear = new Date().getFullYear();
        for (let i = 0; i < yearSelect.options.length; i++) {
            if (yearSelect.options[i].value == currentYear) {
                yearSelect.options[i].selected = true;
                break;
            }
        }
    }
    
    if (monthSelect) {
        // 确保当前月份被选中
        const currentMonth = new Date().getMonth() + 1;
        for (let i = 0; i < monthSelect.options.length; i++) {
            if (monthSelect.options[i].value == currentMonth) {
                monthSelect.options[i].selected = true;
                break;
            }
        }
    }
}

// 初始化表单事件
function initForms() {
    // 添加账号表单
    const addAccountForm = document.getElementById('add-account-form');
    if (addAccountForm) {
        addAccountForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            await addAccount();
        });
    }
    
    // 编辑账号表单
    const editAccountForm = document.getElementById('edit-account-form');
    if (editAccountForm) {
        editAccountForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            await saveEditAccount();
        });
    }
    
    // 设置表单
    const settingsForm = document.getElementById('settings-form');
    if (settingsForm) {
        settingsForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            await saveSettings();
        });
    }
    
    // 保存Cookie按钮
    const saveCookieButton = document.getElementById('save-cookie');
    if (saveCookieButton) {
        saveCookieButton.addEventListener('click', async function() {
            await saveCookie();
        });
    }
    
    // 清空Cookie按钮
    const clearCookieButton = document.getElementById('clear-cookie');
    if (clearCookieButton) {
        clearCookieButton.addEventListener('click', async function() {
            await clearCookie();
        });
    }
    
    // 开始下载按钮
    const startDownloadButton = document.getElementById('start-download');
    if (startDownloadButton) {
        startDownloadButton.addEventListener('click', async function() {
            await startDownload();
        });
    }
    
    // 加载作品列表按钮
    const loadWorksButton = document.getElementById('load-works');
    if (loadWorksButton) {
        loadWorksButton.addEventListener('click', async function() {
            await loadWorks();
        });
    }
    
    // 取消加载作品列表按钮
    const cancelLoadWorksButton = document.getElementById('cancel-load-works');
    if (cancelLoadWorksButton) {
        cancelLoadWorksButton.addEventListener('click', function() {
            cancelLoadWorks();
        });
    }
}

// 加载账号列表
async function loadAccounts() {
    try {
        const response = await axios.get(`${API_BASE_URL}/accounts`);
        const accounts = response.data;
        
        // 更新账号列表
        const accountsList = document.getElementById('accounts-list');
        if (accountsList) {
            accountsList.innerHTML = '';
            accounts.forEach(account => {
                const accountItem = document.createElement('div');
                accountItem.className = 'account-item';
                accountItem.innerHTML = `
                    <h4>${account.mark}</h4>
                    <p>URL: ${account.url}</p>
                    <p>最早发布日期: ${account.earliest}</p>
                    <p>最晚发布日期: ${account.latest}</p>
                    <div class="account-actions">
                        <button onclick="editAccount(${account.id})">编辑</button>
                        <button onclick="deleteAccount(${account.id})">删除</button>
                    </div>
                `;
                accountsList.appendChild(accountItem);
            });
        }
        
        // 更新下载账号选择
        const downloadAccountSelect = document.getElementById('download-account');
        if (downloadAccountSelect) {
            downloadAccountSelect.innerHTML = '';
            accounts.forEach(account => {
                const option = document.createElement('option');
                option.value = account.id;
                option.textContent = account.mark;
                downloadAccountSelect.appendChild(option);
            });
        }
        
        // 更新作品账号选择
        const worksAccountSelect = document.getElementById('works-account');
        if (worksAccountSelect) {
            worksAccountSelect.innerHTML = '';
            accounts.forEach(account => {
                const option = document.createElement('option');
                option.value = account.id;
                option.textContent = account.mark;
                worksAccountSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('加载账号失败:', error);
        addLog('加载账号失败: ' + error.message, 'error');
    }
}

// 添加账号
async function addAccount() {
    try {
        const mark = document.getElementById('mark').value;
        const url = document.getElementById('url').value;
        const earliest = document.getElementById('earliest').value;
        const latest = document.getElementById('latest').value;
        
        const response = await axios.post(`${API_BASE_URL}/accounts`, {
            mark,
            url,
            earliest,
            latest
        });
        
        addLog('账号添加成功!', 'success');
        await loadAccounts();
        
        // 重置表单
        document.getElementById('add-account-form').reset();
    } catch (error) {
        console.error('添加账号失败:', error);
        addLog('添加账号失败: ' + error.message, 'error');
    }
}

// 编辑账号
async function editAccount(accountId) {
    try {
        // 从后端获取账号详情
        const response = await axios.get(`${API_BASE_URL}/accounts/${accountId}`);
        const account = response.data;
        
        // 填充编辑表单
        document.getElementById('edit-account-id').value = account.id;
        document.getElementById('edit-mark').value = account.mark;
        document.getElementById('edit-url').value = account.url;
        document.getElementById('edit-earliest').value = account.earliest;
        document.getElementById('edit-latest').value = account.latest;
        
        // 显示编辑表单
        document.getElementById('edit-account-section').style.display = 'block';
        
        addLog('正在编辑账号: ' + account.mark, 'info');
    } catch (error) {
        console.error('获取账号详情失败:', error);
        addLog('获取账号详情失败: ' + error.message, 'error');
    }
}

// 取消编辑账号
function cancelEditAccount() {
    // 隐藏编辑表单
    document.getElementById('edit-account-section').style.display = 'none';
    addLog('取消编辑账号', 'info');
}

// 保存编辑账号
async function saveEditAccount() {
    try {
        const accountId = document.getElementById('edit-account-id').value;
        const mark = document.getElementById('edit-mark').value;
        const url = document.getElementById('edit-url').value;
        const earliest = document.getElementById('edit-earliest').value;
        const latest = document.getElementById('edit-latest').value;
        
        // 提交修改
        const response = await axios.put(`${API_BASE_URL}/accounts/${accountId}`, {
            mark,
            url,
            earliest,
            latest
        });
        
        addLog('账号编辑成功!', 'success');
        await loadAccounts();
        
        // 隐藏编辑表单
        document.getElementById('edit-account-section').style.display = 'none';
    } catch (error) {
        console.error('编辑账号失败:', error);
        addLog('编辑账号失败: ' + error.message, 'error');
    }
}

// 删除账号
async function deleteAccount(accountId) {
    if (confirm('确定要删除这个账号吗？')) {
        try {
            await axios.delete(`${API_BASE_URL}/accounts/${accountId}`);
            addLog('账号删除成功!', 'success');
            await loadAccounts();
        } catch (error) {
            console.error('删除账号失败:', error);
            addLog('删除账号失败: ' + error.message, 'error');
        }
    }
}

// 加载设置
async function loadSettings() {
    try {
        const response = await axios.get(`${API_BASE_URL}/settings`);
        const settings = response.data;
        
        // 更新设置表单
        const saveFolderInput = document.getElementById('save-folder');
        const downloadVideosInput = document.getElementById('download-videos');
        const downloadImagesInput = document.getElementById('download-images');
        const proxyInput = document.getElementById('proxy');
        const timeoutInput = document.getElementById('timeout');
        
        if (saveFolderInput) saveFolderInput.value = settings.save_folder;
        if (downloadVideosInput) downloadVideosInput.checked = settings.download_videos;
        if (downloadImagesInput) downloadImagesInput.checked = settings.download_images;
        if (proxyInput) proxyInput.value = settings.proxy || '';
        if (timeoutInput) timeoutInput.value = settings.timeout;
    } catch (error) {
        console.error('加载设置失败:', error);
        addLog('加载设置失败: ' + error.message, 'error');
    }
}

// 保存设置
async function saveSettings() {
    try {
        const saveFolder = document.getElementById('save-folder').value;
        const downloadVideos = document.getElementById('download-videos').checked;
        const downloadImages = document.getElementById('download-images').checked;
        const proxy = document.getElementById('proxy').value;
        const timeout = parseInt(document.getElementById('timeout').value);
        
        const response = await axios.put(`${API_BASE_URL}/settings`, {
            save_folder: saveFolder,
            download_videos: downloadVideos,
            download_images: downloadImages,
            proxy: proxy,
            timeout: timeout
        });
        
        addLog('设置保存成功!', 'success');
    } catch (error) {
        console.error('保存设置失败:', error);
        addLog('保存设置失败: ' + error.message, 'error');
    }
}

// 加载Cookie
async function loadCookie() {
    try {
        const response = await axios.get(`${API_BASE_URL}/cookie`);
        const cookie = response.data;
        
        // 更新Cookie输入
        const cookieInput = document.getElementById('cookie-input');
        if (cookieInput) {
            // 将cookie字典转换为字符串格式
            const cookieString = Object.entries(cookie.cookies)
                .map(([key, value]) => `${key}=${value}`)
                .join('; ');
            cookieInput.value = cookieString;
        }
    } catch (error) {
        console.error('加载Cookie失败:', error);
        addLog('加载Cookie失败: ' + error.message, 'error');
    }
}

// 保存Cookie
async function saveCookie() {
    try {
        const cookieInput = document.getElementById('cookie-input');
        const cookieValue = cookieInput.value;
        
        // 直接发送cookie值，后端会自动处理
        const response = await axios.put(`${API_BASE_URL}/cookie`, {
            cookies: cookieValue
        });
        
        addLog('Cookie保存成功!', 'success');
    } catch (error) {
        console.error('保存Cookie失败:', error);
        addLog('保存Cookie失败: ' + error.message, 'error');
    }
}

// 清空Cookie
async function clearCookie() {
    try {
        // 调用后端API删除Cookie
        const response = await axios.delete(`${API_BASE_URL}/cookie`);
        
        // 清空输入框
        const cookieInput = document.getElementById('cookie-input');
        if (cookieInput) {
            cookieInput.value = '';
        }
        
        addLog('Cookie已清空!', 'success');
    } catch (error) {
        console.error('清空Cookie失败:', error);
        addLog('清空Cookie失败: ' + error.message, 'error');
    }
}

// 开始下载
async function startDownload() {
    try {
        const accountId = document.getElementById('download-account').value;
        
        // 这里可以添加选择作品的逻辑
        // 暂时下载所有作品
        const workIds = [];
        
        const response = await axios.post(`${API_BASE_URL}/download`, {
            account_id: parseInt(accountId),
            work_ids: workIds
        });
        
        const downloadResponse = response.data;
        addLog(`下载任务已启动，任务ID: ${downloadResponse.task_id}`, 'info');
        
        // 显示下载状态
        const downloadStatus = document.getElementById('download-status');
        if (downloadStatus) {
            downloadStatus.innerHTML = `
                <p>任务ID: ${downloadResponse.task_id}</p>
                <p>状态: ${downloadResponse.status}</p>
                <p>进度: ${downloadResponse.progress}%</p>
                <p>已完成: ${downloadResponse.completed_count}/${downloadResponse.total_count}</p>
            `;
        }
        
        // 轮询下载状态
        pollDownloadStatus(downloadResponse.task_id);
    } catch (error) {
        console.error('开始下载失败:', error);
        addLog('开始下载失败: ' + error.message, 'error');
    }
}

// 轮询下载状态
async function pollDownloadStatus(taskId) {
    try {
        const response = await axios.get(`${API_BASE_URL}/download/status/${taskId}`);
        const status = response.data;
        
        // 更新下载状态
        const downloadStatus = document.getElementById('download-status');
        if (downloadStatus) {
            downloadStatus.innerHTML = `
                <p>任务ID: ${status.task_id}</p>
                <p>状态: ${status.status}</p>
                <p>进度: ${status.progress}%</p>
                <p>已完成: ${status.completed_count}/${status.total_count}</p>
                <p>消息: ${status.message || ''}</p>
            `;
        }
        
        // 如果下载未完成，继续轮询
        if (status.status !== 'completed' && status.status !== 'failed') {
            setTimeout(() => pollDownloadStatus(taskId), 2000);
        } else {
            addLog(`下载任务 ${status.status}: ${status.message || ''}`, status.status === 'completed' ? 'success' : 'error');
        }
    } catch (error) {
        console.error('获取下载状态失败:', error);
        addLog('获取下载状态失败: ' + error.message, 'error');
    }
}

// 加载作品列表
async function loadWorks() {
    try {
        // 重置之前的加载状态
        if (loadWorksAbortController) {
            loadWorksAbortController.abort();
        }
        if (loadWorksProgressInterval) {
            clearInterval(loadWorksProgressInterval);
        }
        
        // 创建新的AbortController
        loadWorksAbortController = new AbortController();
        
        // 更新UI状态
        document.getElementById('works-loading').style.display = 'block';
        document.getElementById('load-works').disabled = true;
        document.getElementById('cancel-load-works').disabled = false;
        document.getElementById('works-progress-bar').style.width = '0%';
        document.getElementById('works-progress-text').textContent = '0%';
        
        // 模拟进度更新
        let progress = 0;
        loadWorksProgressInterval = setInterval(() => {
            if (progress < 90) {
                progress += 5;
                document.getElementById('works-progress-bar').style.width = `${progress}%`;
                document.getElementById('works-progress-text').textContent = `${progress}%`;
            }
        }, 200);
        
        // 获取选择的账号
        const accountId = document.getElementById('works-account').value;
        
        // 检查是否启用年份月份筛选
        const useYearMonthFilter = document.getElementById('use-year-month').checked;
        
        // 计算日期范围
        let earliest = null;
        let latest = null;
        
        if (useYearMonthFilter) {
            // 获取选择的年份和月份
            const year = parseInt(document.getElementById('works-year').value);
            const month = parseInt(document.getElementById('works-month').value);
            
            if (year && month) {
                // 计算当月的第一天和最后一天
                const firstDay = new Date(year, month - 1, 1);
                const lastDay = new Date(year, month, 0);
                
                // 格式化日期，避免时区问题
                function formatDate(date) {
                    const year = date.getFullYear();
                    const month = String(date.getMonth() + 1).padStart(2, '0');
                    const day = String(date.getDate()).padStart(2, '0');
                    return `${year}-${month}-${day}`;
                }
                
                earliest = formatDate(firstDay);
                latest = formatDate(lastDay);
            }
        }
        
        // 构建请求参数
        const params = {
            account_id: parseInt(accountId),
            page: 1,
            page_size: 50
        };
        
        // 如果启用了年份月份筛选且有日期范围，添加到参数中
        if (useYearMonthFilter && earliest && latest) {
            params.earliest = earliest;
            params.latest = latest;
        }
        
        // 发送请求
        const response = await axios.get(`${API_BASE_URL}/works`, {
            params: params,
            signal: loadWorksAbortController.signal
        });
        
        // 清除进度更新
        if (loadWorksProgressInterval) {
            clearInterval(loadWorksProgressInterval);
            loadWorksProgressInterval = null;
        }
        
        // 更新进度为100%
        document.getElementById('works-progress-bar').style.width = '100%';
        document.getElementById('works-progress-text').textContent = '100%';
        
        const worksResponse = response.data;
        const works = worksResponse.items;
        
        // 更新作品列表
        const worksList = document.getElementById('works-list');
        if (worksList) {
            worksList.innerHTML = '';
            if (works.length > 0) {
                // 添加批量下载按钮
                const batchDownloadSection = document.createElement('div');
                batchDownloadSection.className = 'batch-download-section';
                batchDownloadSection.innerHTML = `
                    <div class="batch-download-controls">
                        <button onclick="selectAllWorks()">全选</button>
                        <button onclick="deselectAllWorks()">取消全选</button>
                        <button onclick="batchDownloadWorks()">批量下载</button>
                        <span id="selected-count">已选择: 0</span>
                    </div>
                `;
                worksList.appendChild(batchDownloadSection);
                
                const worksGrid = document.createElement('div');
                worksGrid.className = 'works-grid';
                
                // 存储作品信息，用于下载
                const worksMap = new Map();
                
                works.forEach(work => {
                    // 存储作品信息
                    worksMap.set(work.id, work);
                    
                    const workItem = document.createElement('div');
                    workItem.className = 'work-item';
                    
                    // 构建视频代理URL
                    let videoElement = '';
                    if (work.cover_url) {
                        if (work.type === '视频' && Array.isArray(work.downloads) && work.downloads[0]) {
                            const videoUrl = work.downloads[0];
                            const proxyUrl = `/api/proxy/video?url=${encodeURIComponent(videoUrl)}`;
                            videoElement = `<video src="${proxyUrl}" poster="${work.cover_url}" controls preload="metadata" onerror="handleVideoError(this)"></video>`;
                        } else if (work.type === '视频') {
                            videoElement = `<div class="work-cover-placeholder">视频链接无效</div>`;
                        } else {
                            videoElement = `<img src="${work.cover_url}" alt="${work.desc}">`;
                        }
                    } else {
                        videoElement = `<div class="work-cover-placeholder">无封面</div>`;
                    }
                    
                    workItem.innerHTML = `
                        <div class="work-checkbox">
                            <input type="checkbox" class="work-select" data-id="${work.id}" onchange="updateSelectedCount()">
                        </div>
                        <div class="work-cover">
                            ${videoElement}
                        </div>
                        <h4>${work.desc}</h4>
                        <p>类型: ${work.type}</p>
                        <p>创建时间: ${new Date(work.create_time).toLocaleString()}</p>
                        <p>分辨率: ${work.width}×${work.height}</p>
                        <div class="work-actions">
                            <button onclick="previewWork('${work.id}')">预览</button>
                            <button onclick="downloadWork('${work.id}')">下载</button>
                        </div>
                    `;
                    worksGrid.appendChild(workItem);
                });
                
                // 将worksMap存储到全局变量中，供downloadWork函数使用
                window.worksMap = worksMap;
                
                worksList.appendChild(worksGrid);
            } else {
                worksList.innerHTML = '<p>暂无作品</p>';
            }
        }
        
        addLog(`加载作品列表成功，共 ${works.length} 个作品`, 'info');
    } catch (error) {
        // 清除进度更新
        if (loadWorksProgressInterval) {
            clearInterval(loadWorksProgressInterval);
            loadWorksProgressInterval = null;
        }
        
        if (error.name === 'AbortError') {
            addLog('加载作品列表已取消', 'info');
        } else {
            console.error('加载作品列表失败:', error);
            addLog('加载作品列表失败: ' + error.message, 'error');
        }
    } finally {
        // 恢复UI状态
        document.getElementById('works-loading').style.display = 'none';
        document.getElementById('load-works').disabled = false;
        document.getElementById('cancel-load-works').disabled = true;
        
        // 重置全局变量
        loadWorksAbortController = null;
        loadWorksProgressInterval = null;
    }
}

// 取消加载作品列表
function cancelLoadWorks() {
    if (loadWorksAbortController) {
        loadWorksAbortController.abort();
        addLog('正在取消加载作品列表...', 'info');
    }
}

// 下载单个作品
async function downloadWork(workId) {
    try {
        const accountId = document.getElementById('works-account').value;
        
        // 从全局变量中获取作品信息
        const work = window.worksMap ? window.worksMap.get(workId) : null;
        
        // 打印调试信息
        console.log('下载作品:', {
            workId: workId,
            accountId: accountId,
            work: work,
            url: `${API_BASE_URL}/download`
        });
        
        // 确保workId是字符串
        if (typeof workId !== 'string') {
            workId = String(workId);
            console.log('转换workId为字符串:', workId);
        }
        
        // 构建请求数据
        const requestData = {
            account_id: parseInt(accountId),
            work_ids: [workId]
        };
        
        // 如果有作品信息，添加到请求数据中
        if (work) {
            requestData.works = [work];
            console.log('已添加作品信息到请求数据中');
        }
        
        const response = await axios.post(`${API_BASE_URL}/download/`, requestData);
        
        const downloadResponse = response.data;
        console.log('下载响应:', downloadResponse);
        addLog(`下载任务已启动，任务ID: ${downloadResponse.task_id}`, 'info');
        
        // 轮询下载状态
        pollDownloadStatus(downloadResponse.task_id);
    } catch (error) {
        console.error('下载作品失败:', error);
        addLog('下载作品失败: ' + error.message, 'error');
    }
}

// 全选所有作品
function selectAllWorks() {
    const checkboxes = document.querySelectorAll('.work-select');
    checkboxes.forEach(checkbox => {
        checkbox.checked = true;
    });
    updateSelectedCount();
    addLog('已全选所有作品', 'info');
}

// 取消全选所有作品
function deselectAllWorks() {
    const checkboxes = document.querySelectorAll('.work-select');
    checkboxes.forEach(checkbox => {
        checkbox.checked = false;
    });
    updateSelectedCount();
    addLog('已取消全选所有作品', 'info');
}

// 更新已选择作品的数量
function updateSelectedCount() {
    const checkboxes = document.querySelectorAll('.work-select:checked');
    const count = checkboxes.length;
    const selectedCountElement = document.getElementById('selected-count');
    if (selectedCountElement) {
        selectedCountElement.textContent = `已选择: ${count}`;
    }
}

// 批量下载选中的作品
async function batchDownloadWorks() {
    try {
        const accountId = document.getElementById('works-account').value;
        const checkboxes = document.querySelectorAll('.work-select:checked');
        
        if (checkboxes.length === 0) {
            addLog('请至少选择一个作品进行下载', 'warning');
            return;
        }
        
        // 获取选中的作品ID和作品信息
        const workIds = [];
        const works = [];
        
        checkboxes.forEach(checkbox => {
            const workId = checkbox.getAttribute('data-id');
            workIds.push(workId);
            
            // 从全局变量中获取作品信息
            const work = window.worksMap ? window.worksMap.get(workId) : null;
            if (work) {
                works.push(work);
            }
        });
        
        // 构建请求数据
        const requestData = {
            account_id: parseInt(accountId),
            work_ids: workIds
        };
        
        // 如果有作品信息，添加到请求数据中
        if (works.length > 0) {
            requestData.works = works;
            console.log('已添加作品信息到请求数据中');
        }
        
        addLog(`开始批量下载 ${workIds.length} 个作品...`, 'info');
        
        const response = await axios.post(`${API_BASE_URL}/download/`, requestData);
        const downloadResponse = response.data;
        
        addLog(`批量下载任务已启动，任务ID: ${downloadResponse.task_id}`, 'info');
        
        // 轮询下载状态
        pollDownloadStatus(downloadResponse.task_id);
    } catch (error) {
        console.error('批量下载失败:', error);
        addLog('批量下载失败: ' + error.message, 'error');
    }
}

// 添加日志
function addLog(message, type = 'info') {
    const logsContent = document.getElementById('logs-content');
    if (logsContent) {
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${type}`;
        logEntry.textContent = `[${new Date().toLocaleString()}] ${message}`;
        logsContent.appendChild(logEntry);
        
        // 滚动到底部
        logsContent.scrollTop = logsContent.scrollHeight;
    }
    
    // 同时输出到控制台
    console.log(`[${type}] ${message}`);
}

// 加载当前配置
async function loadCurrentConfig() {
    try {
        const response = await axios.get(`${API_BASE_URL}/config`);
        const config = response.data;
        
        // 更新当前配置显示
        const currentConfig = document.getElementById('current-config');
        if (currentConfig) {
            currentConfig.textContent = JSON.stringify(config, null, 2);
        }
    } catch (error) {
        console.error('加载当前配置失败:', error);
        addLog('加载当前配置失败: ' + error.message, 'error');
    }
}

// 绑定配置管理事件监听器
function bindConfigEventListeners() {
    // 导入配置按钮
    const importConfigButton = document.getElementById('import-config');
    if (importConfigButton) {
        importConfigButton.addEventListener('click', importConfig);
    }
    
    // 导入配置文件输入
    const importConfigFileInput = document.getElementById('import-config-file');
    if (importConfigFileInput) {
        importConfigFileInput.addEventListener('change', handleImportConfigFile);
    }
    
    // 导出当前配置按钮
    const exportConfigButton = document.getElementById('export-config');
    if (exportConfigButton) {
        exportConfigButton.addEventListener('click', exportConfig);
    }
    
    // 初始化配置按钮
    const initConfigButton = document.getElementById('init-config');
    if (initConfigButton) {
        initConfigButton.addEventListener('click', initConfig);
    }
}

// 处理导入配置文件
function handleImportConfigFile(e) {
    const file = e.target.files[0];
    if (!file) {
        return;
    }
    
    const reader = new FileReader();
    reader.onload = function(e) {
        const content = e.target.result;
        const importConfigInput = document.getElementById('import-config-input');
        if (importConfigInput) {
            importConfigInput.value = content;
        }
    };
    reader.readAsText(file);
}

// 导入配置
async function importConfig() {
    try {
        const configInput = document.getElementById('import-config-input');
        const configContent = configInput.value;
        
        if (!configContent) {
            addLog('请输入配置内容', 'warning');
            return;
        }
        
        // 解析配置内容
        const config = JSON.parse(configContent);
        
        // 调用后端API导入配置
        const response = await axios.post(`${API_BASE_URL}/config/import`, config);
        
        addLog('配置导入成功!', 'success');
        await loadCurrentConfig();
    } catch (error) {
        console.error('导入配置失败:', error);
        addLog('导入配置失败: ' + error.message, 'error');
    }
}

// 导出配置
async function exportConfig() {
    try {
        // 获取当前配置
        const response = await axios.get(`${API_BASE_URL}/config`);
        const config = response.data;
        
        // 将配置转换为JSON字符串
        const configJson = JSON.stringify(config, null, 2);
        
        // 创建Blob对象
        const blob = new Blob([configJson], { type: 'application/json' });
        
        // 尝试使用showSaveFilePicker API（现代浏览器支持）
        if (window.showSaveFilePicker) {
            try {
                const handle = await window.showSaveFilePicker({
                    suggestedName: `douyin_download_config_${new Date().toISOString().slice(0, 10)}.json`,
                    types: [
                        {
                            description: 'JSON文件',
                            accept: {
                                'application/json': ['.json']
                            }
                        }
                    ]
                });
                
                const writable = await handle.createWritable();
                await writable.write(blob);
                await writable.close();
                
                addLog('配置导出成功!', 'success');
            } catch (err) {
                // 用户取消了文件选择
                if (err.name === 'AbortError') {
                    addLog('配置导出已取消', 'info');
                    return;
                }
                // 回退到传统下载方式
                fallbackDownload(blob);
            }
        } else {
            // 回退到传统下载方式
            fallbackDownload(blob);
        }
    } catch (error) {
        console.error('导出配置失败:', error);
        addLog('导出配置失败: ' + error.message, 'error');
    }
}

// 传统下载方式（浏览器不支持showSaveFilePicker时使用）
function fallbackDownload(blob) {
    // 创建下载链接
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `douyin_download_config_${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(a);
    
    // 触发下载
    a.click();
    
    // 清理
    setTimeout(() => {
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }, 100);
    
    addLog('配置导出成功! 请在浏览器的下载对话框中选择保存路径。', 'success');
}

// 初始化配置
async function initConfig() {
    if (confirm('确定要初始化配置吗？这将重置所有配置为默认值。')) {
        try {
            // 调用后端API初始化配置
            const response = await axios.post(`${API_BASE_URL}/config/init`);
            
            addLog('配置初始化成功!', 'success');
            await loadCurrentConfig();
        } catch (error) {
            console.error('初始化配置失败:', error);
            addLog('初始化配置失败: ' + error.message, 'error');
        }
    }
}

// 预览作品
function previewWork(workId) {
    const work = window.worksMap ? window.worksMap.get(workId) : null;
    if (!work) return;
    
    // 创建预览模态框
    let modal = document.getElementById('preview-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'preview-modal';
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <span class="close">&times;</span>
                <div id="preview-content"></div>
            </div>
        `;
        document.body.appendChild(modal);
        
        // 添加关闭事件
        modal.querySelector('.close').addEventListener('click', function() {
            // 暂停并移除视频元素
            const video = modal.querySelector('video');
            if (video) {
                video.pause();
                video.src = ''; // 清空视频源，释放资源
                video.remove(); // 从DOM中移除视频元素
            }
            // 清空预览内容
            const previewContent = document.getElementById('preview-content');
            if (previewContent) {
                previewContent.innerHTML = '';
            }
            modal.style.display = 'none';
        });
        
        // 点击模态框外部关闭
        window.addEventListener('click', function(event) {
            if (event.target === modal) {
                // 暂停并移除视频元素
                const video = modal.querySelector('video');
                if (video) {
                    video.pause();
                    video.src = ''; // 清空视频源，释放资源
                    video.remove(); // 从DOM中移除视频元素
                }
                // 清空预览内容
                const previewContent = document.getElementById('preview-content');
                if (previewContent) {
                    previewContent.innerHTML = '';
                }
                modal.style.display = 'none';
            }
        });
    }
    
    const previewContent = document.getElementById('preview-content');
    if (work.type === '视频') {
        const videoUrl = Array.isArray(work.downloads) ? work.downloads[0] : work.downloads;
        if (videoUrl) {
            // 使用代理接口加载视频，绕过CORS限制
            const proxyUrl = `/api/proxy/video?url=${encodeURIComponent(videoUrl)}`;
            // 添加视频加载错误处理
            previewContent.innerHTML = `
                <div id="video-container">
                    <video src="${proxyUrl}" controls autoplay width="100%" onerror="handleVideoError(this)"></video>
                    <div id="video-error" style="display: none; text-align: center; padding: 20px; color: #999;">
                        <h3>视频加载失败</h3>
                        <p>无法加载此视频，请检查网络连接或视频链接是否有效。</p>
                        <p>视频链接: <a href="${videoUrl}" target="_blank">${videoUrl}</a></p>
                        <button onclick="copyVideoUrl('${videoUrl}')">复制视频链接</button>
                        <button onclick="downloadVideoDirect('${videoUrl}')">直接下载</button>
                    </div>
                </div>
                <h3>${work.desc}</h3>
                <p>类型: ${work.type}</p>
                <p>创建时间: ${new Date(work.create_time).toLocaleString()}</p>
                <p>分辨率: ${work.width}×${work.height}</p>
                <p>视频链接: <a href="${videoUrl}" target="_blank">${videoUrl}</a></p>
                <p>代理链接: <a href="${proxyUrl}" target="_blank">${proxyUrl}</a></p>
            `;
            
            // 添加视频加载事件监听器
            setTimeout(() => {
                const video = document.querySelector('#video-container video');
                if (video) {
                    video.addEventListener('loadedmetadata', function() {
                        console.log('视频元数据加载成功');
                    });
                    video.addEventListener('error', function(e) {
                        console.error('视频加载错误:', e);
                        handleVideoError(this);
                    });
                }
            }, 100);
        } else {
            previewContent.innerHTML = `
                <div style="text-align: center; padding: 50px; color: #999;">
                    <h3>视频链接无效</h3>
                    <p>无法预览此视频，因为视频链接无效或不存在。</p>
                </div>
                <h3>${work.desc}</h3>
                <p>类型: ${work.type}</p>
                <p>创建时间: ${new Date(work.create_time).toLocaleString()}</p>
                <p>分辨率: ${work.width}×${work.height}</p>
            `;
        }
    } else {
        let imagesHtml = '';
        if (Array.isArray(work.downloads)) {
            work.downloads.forEach((download, index) => {
                if (Array.isArray(download)) {
                    // 图集格式: [url, width, height]
                    imagesHtml += `<img src="${download[0]}" style="max-width: 100%; margin: 10px 0;">`;
                } else {
                    // 其他格式
                    imagesHtml += `<img src="${download}" style="max-width: 100%; margin: 10px 0;">`;
                }
            });
        } else {
            imagesHtml = `<img src="${work.downloads}" style="max-width: 100%;">`;
        }
        previewContent.innerHTML = `
            ${imagesHtml}
            <h3>${work.desc}</h3>
            <p>类型: ${work.type}</p>
            <p>创建时间: ${new Date(work.create_time).toLocaleString()}</p>
            <p>分辨率: ${work.width}×${work.height}</p>
        `;
    }
    
    modal.style.display = 'block';
}

// 处理视频加载错误
function handleVideoError(videoElement) {
    // 添加详细的调试信息
    console.error('视频加载错误:', videoElement.error);
    console.log('视频元素src:', videoElement.src);
    console.log('当前页面URL:', window.location.href);
    console.log('视频元素duration:', videoElement.duration);
    console.log('视频元素readyState:', videoElement.readyState);
    console.log('视频元素网络状态:', videoElement.networkState);
    
    // 检查视频是否已经成功加载（例如，已经有了duration属性）
    if (videoElement.duration > 0) {
        // 视频已经成功加载，可能只是暂时的错误
        console.log('视频已经成功加载，忽略错误');
        return;
    }
    
    // 检查视频URL是否是当前页面的URL或前端页面的URL
    const currentPageUrl = window.location.href;
    const frontendUrl = currentPageUrl.includes('/frontend') ? currentPageUrl : currentPageUrl + '/frontend';
    
    console.log('检查URL匹配:', videoElement.src, '===', currentPageUrl, '?', videoElement.src === currentPageUrl);
    console.log('检查URL匹配:', videoElement.src, '===', frontendUrl, '?', videoElement.src === frontendUrl);
    
    if (videoElement.src === currentPageUrl || videoElement.src === frontendUrl) {
        // 视频URL是当前页面的URL，可能是因为视频元素被从DOM中移除导致的，忽略错误
        console.log('视频URL是当前页面的URL，忽略错误');
        return;
    }
    
    // 检查视频URL是否为空或无效
    if (!videoElement.src || videoElement.src === '') {
        // 视频URL为空，可能是因为视频元素被重置，忽略错误
        console.log('视频URL为空，忽略错误');
        return;
    }
    
    // 检查视频URL是否包含'frontend'（可能是错误的URL）
    if (videoElement.src.includes('/frontend')) {
        // 视频URL包含'frontend'，可能是因为错误的URL，忽略错误
        console.log('视频URL包含frontend，忽略错误');
        return;
    }
    
    // 显示错误信息
    const errorContainer = videoElement.nextElementSibling;
    if (errorContainer && errorContainer.id === 'video-error') {
        errorContainer.style.display = 'block';
    }
    
    // 隐藏视频元素
    videoElement.style.display = 'none';
    
    // 获取视频URL（如果可用）
    const videoUrl = videoElement.src;
    const errorMessage = videoUrl ? `视频加载失败: ${videoUrl}` : '视频加载失败，请检查网络连接或视频链接是否有效';
    addLog(errorMessage, 'error');
}

// 复制视频链接到剪贴板
function copyVideoUrl(videoUrl) {
    if (navigator.clipboard && window.isSecureContext) {
        // 现代浏览器
        navigator.clipboard.writeText(videoUrl).then(function() {
            addLog('视频链接已复制到剪贴板', 'success');
        }).catch(function(err) {
            console.error('复制失败:', err);
            addLog('复制视频链接失败，请手动复制', 'error');
        });
    } else {
        // 回退方法
        const textArea = document.createElement('textarea');
        textArea.value = videoUrl;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        try {
            document.execCommand('copy');
            addLog('视频链接已复制到剪贴板', 'success');
        } catch (err) {
            console.error('复制失败:', err);
            addLog('复制视频链接失败，请手动复制', 'error');
        } finally {
            document.body.removeChild(textArea);
        }
    }
}

// 直接下载视频
function downloadVideoDirect(videoUrl) {
    try {
        // 创建下载链接
        const a = document.createElement('a');
        a.href = videoUrl;
        a.download = `video_${Date.now()}.mp4`;
        document.body.appendChild(a);
        
        // 触发下载
        a.click();
        
        // 清理
        setTimeout(() => {
            document.body.removeChild(a);
        }, 100);
        
        addLog('正在开始直接下载视频', 'info');
    } catch (error) {
        console.error('直接下载失败:', error);
        addLog('直接下载视频失败，请手动下载', 'error');
    }
}

// 添加CSS样式
function addPreviewStyles() {
    const style = document.createElement('style');
    style.innerHTML = `
        /* 预览模态框 */
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            overflow: auto;
            background-color: rgba(0, 0, 0, 0.9);
        }
        
        .modal-content {
            background-color: #fefefe;
            margin: 5% auto;
            padding: 20px;
            border: 1px solid #888;
            width: 80%;
            max-width: 800px;
            border-radius: 8px;
            position: relative;
        }
        
        .close {
            color: #aaa;
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }
        
        .close:hover,
        .close:focus {
            color: black;
            text-decoration: none;
            cursor: pointer;
        }
        
        /* 作品封面 */
        .work-cover {
            width: 100%;
            height: 150px;
            overflow: hidden;
            border-radius: 4px;
            margin-bottom: 10px;
            background-color: #f0f0f0;
        }
        
        .work-cover video {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        
        .work-cover img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        
        .work-cover-placeholder {
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #999;
            font-size: 14px;
        }
        
        /* 作品网格 */
        .works-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .work-item {
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            transition: box-shadow 0.3s ease;
            position: relative;
        }
        
        .work-item:hover {
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
        }
        
        .work-checkbox {
            position: absolute;
            top: 10px;
            right: 10px;
        }
        
        .work-actions {
            margin-top: 15px;
            display: flex;
            gap: 10px;
        }
        
        .work-actions button {
            padding: 8px 12px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }
        
        .work-actions button:first-child {
            background-color: #4CAF50;
            color: white;
        }
        
        .work-actions button:first-child:hover {
            background-color: #45a049;
        }
        
        .work-actions button:last-child {
            background-color: #008CBA;
            color: white;
        }
        
        .work-actions button:last-child:hover {
            background-color: #007B9E;
        }
    `;
    document.head.appendChild(style);
}

// 页面加载时添加样式
window.addEventListener('load', addPreviewStyles);


