# 抖音作品下载工具优化方案

## 1. 优化目标

- **减少获取时间**：大幅减少作品获取时间，特别是对于特定日期范围的作品
- **提高系统稳定性**：增强系统对大量作品的处理能力
- **提升用户体验**：添加详细的加载状态和进度反馈
- **优化内存使用**：减少不必要的内存消耗

## 2. 核心优化点

### 2.1 后端优化

#### 2.1.1 API参数优化

- **添加时间相关参数**：
  - `time_list_query=1`
  - `need_time_list=0`
  - `from_user_page=1`

- **使用正确的时间戳**：
  - 将日期转换为毫秒级时间戳
  - 设置 `max_cursor` 和 `forward_end_cursor` 参数

- **增加请求数量**：
  - 将 `count` 参数从20增加到50
  - 减少总请求次数

#### 2.1.2 缓存机制

- **实现作品缓存**：
  - 使用本地文件缓存已经获取的作品列表
  - 缓存键设计：`sec_user_id + earliest_date + latest_date`
  - 过期时间：1小时

#### 2.1.3 分页优化

- **修改分页逻辑**：
  - 保留使用 `has_more` 字段和 `max_cursor` 进行分页
  - 移除基于作品顺序的停止逻辑

### 2.2 前端优化

#### 2.2.1 日期选择器优化

- **添加年份月份选择**：
  - 实现类似抖音网页版的年份月份选择器
  - 支持快捷时间范围选择

#### 2.2.2 加载状态优化

- **添加进度条**：
  - 显示详细的获取进度
  - 估算剩余时间

- **添加取消按钮**：
  - 允许用户取消长时间的获取操作

## 3. 技术实现方案

### 3.1 后端实现

**修改 `src/download/acquire.py` 文件**：

```python
def request_items(self, sec_user_id: str, earliest_date: date, latest_date: date, settings: Settings, cookie: Cookie) -> list[dict] | None:
    '''请求并返回所有作品数据'''
    try:
        items = []
        self.cursor = 0
        self.finished = False
        retry_count = 0
        max_retries = 3

        logger.info('开始获取作品列表...')
        
        while not self.finished and retry_count < max_retries:
            # 构建完整的请求参数，包含必要的设备和应用信息
            params = {
                'sec_user_id': sec_user_id,
                'max_cursor': self.cursor,
                'count': 50,  # 增加请求数量
                'cut_version': 1,
                'publish_video_strategy_type': 2,
                'source': 'page',
                'time_list_query': 1,
                'need_time_list': 0,
                'from_user_page': 1,
                # 其他设备和应用信息...
            }
            
            # 转换日期为毫秒级时间戳
            if earliest_date:
                params['max_cursor'] = int(earliest_date.timestamp() * 1000)
            if latest_date:
                params['forward_end_cursor'] = int(latest_date.timestamp() * 1000)
            
            # 其他请求逻辑...
```

**添加缓存功能**：

```python
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
    cache_file = Path("./cache") / f"{cache_key}.json"
    if cache_file.exists():
        try:
            # 检查缓存是否过期
            if (datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)).total_seconds() < 3600:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
    return None

def _save_cache(self, cache_key: str, items: list[dict]):
    '''保存缓存'''
    cache_dir = Path("./cache")
    cache_dir.mkdir(exist_ok=True)
    cache_file = cache_dir / f"{cache_key}.json"
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
```

### 3.2 前端实现

**修改 `frontend/index.html` 文件**：

```html
<!-- 添加年份月份选择器 -->
<div class="form-group">
    <label>日期选择方式</label>
    <select id="date-mode">
        <option value="calendar">日历选择</option>
        <option value="year-month">年份月份选择</option>
    </select>
</div>

<!-- 年份月份选择器 -->
<div id="year-month-selector" style="display: none;">
    <div class="form-group">
        <label for="select-year">选择年份</label>
        <select id="select-year"></select>
    </div>
    <div class="form-group">
        <label for="select-month">选择月份</label>
        <select id="select-month">
            <option value="1">1月</option>
            <option value="2">2月</option>
            <option value="3">3月</option>
            <option value="4">4月</option>
            <option value="5">5月</option>
            <option value="6">6月</option>
            <option value="7">7月</option>
            <option value="8">8月</option>
            <option value="9">9月</option>
            <option value="10">10月</option>
            <option value="11">11月</option>
            <option value="12">12月</option>
        </select>
    </div>
</div>

<!-- 加载状态 -->
<div id="loading-status" style="display: none;">
    <div class="progress">
        <div class="progress-bar" role="progressbar" style="width: 0%" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100"></div>
    </div>
    <p id="loading-text">加载中...</p>
    <button id="cancel-load" class="btn btn-secondary">取消</button>
</div>
```

**修改 `frontend/script.js` 文件**：

```javascript
// 年份月份选择器逻辑
document.getElementById('date-mode').addEventListener('change', function() {
    const mode = this.value;
    const calendarSelector = document.getElementById('calendar-selector');
    const yearMonthSelector = document.getElementById('year-month-selector');
    
    if (mode === 'calendar') {
        calendarSelector.style.display = 'block';
        yearMonthSelector.style.display = 'none';
    } else {
        calendarSelector.style.display = 'none';
        yearMonthSelector.style.display = 'block';
    }
});

// 生成年份选项
function generateYearOptions() {
    const yearSelect = document.getElementById('select-year');
    const currentYear = new Date().getFullYear();
    
    for (let year = currentYear; year >= 2020; year--) {
        const option = document.createElement('option');
        option.value = year;
        option.textContent = year + '年';
        yearSelect.appendChild(option);
    }
}

// 加载状态更新
function updateLoadingStatus(progress, text) {
    const progressBar = document.querySelector('.progress-bar');
    const loadingText = document.getElementById('loading-text');
    
    if (progressBar) {
        progressBar.style.width = progress + '%';
        progressBar.setAttribute('aria-valuenow', progress);
    }
    
    if (loadingText) {
        loadingText.textContent = text;
    }
}
```

## 4. 测试方案

### 4.1 单元测试

- **测试API参数**：验证添加的时间相关参数是否有效
- **测试缓存机制**：验证缓存是否正确加载和保存
- **测试分页逻辑**：验证分页机制是否正常工作

### 4.2 集成测试

- **测试作品获取**：验证能否获取完整的作品列表
- **测试日期筛选**：验证能否正确筛选指定日期范围内的作品
- **测试系统稳定性**：验证系统能否处理大量作品

### 4.3 性能测试

- **测试获取时间**：比较优化前后的获取时间
- **测试内存使用**：监控优化前后的内存使用情况
- **测试网络流量**：比较优化前后的网络流量

## 5. 实施计划

### 5.1 阶段一：后端优化

1. **修改 `src/download/acquire.py` 文件**：
   - 添加时间相关参数
   - 实现缓存机制
   - 优化分页逻辑

2. **测试后端优化**：
   - 运行单元测试
   - 运行集成测试
   - 运行性能测试

### 5.2 阶段二：前端优化

1. **修改 `frontend/index.html` 文件**：
   - 添加年份月份选择器
   - 添加加载状态和进度条

2. **修改 `frontend/script.js` 文件**：
   - 添加年份月份选择器逻辑
   - 添加加载状态更新逻辑

3. **测试前端优化**：
   - 测试日期选择器功能
   - 测试加载状态显示
   - 测试取消按钮功能

### 5.3 阶段三：系统集成测试

1. **运行完整测试**：
   - 测试端到端功能
   - 测试系统稳定性
   - 测试用户体验

2. **优化调整**：
   - 根据测试结果进行调整
   - 优化系统性能

## 6. 预期效果

### 6.1 性能提升

- **获取时间**：减少50-80%
- **网络流量**：减少60-90%
- **系统稳定性**：提升50%

### 6.2 用户体验提升

- **加载状态**：详细的进度显示
- **日期选择**：更加灵活的选择方式
- **操作反馈**：及时的操作反馈

### 6.3 系统可靠性提升

- **错误处理**：更加健壮的错误处理
- **缓存机制**：减少重复获取的可能性
- **分页逻辑**：更加稳定的分页机制

## 7. 风险评估

### 7.1 潜在风险

- **API兼容性**：抖音API可能会变化
- **缓存一致性**：缓存可能与实际数据不一致
- **前端兼容性**：不同浏览器可能有不同的表现

### 7.2 风险缓解

- **API兼容性**：添加API响应验证和错误处理
- **缓存一致性**：设置合理的缓存过期时间
- **前端兼容性**：使用标准的HTML5和JavaScript

## 8. 结论

本优化方案通过修改API参数、实现缓存机制和优化前端界面，旨在大幅提升抖音作品下载工具的性能和用户体验。预期可以减少50-80%的获取时间，提高系统稳定性，提升用户体验。

实施过程将分为三个阶段：后端优化、前端优化和系统集成测试。每个阶段都会进行详细的测试，确保优化效果符合预期。