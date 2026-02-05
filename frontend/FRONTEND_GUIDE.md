# Web Agent Frontend - 使用指南

一个现代化的 Web Agent 控制界面，具有科技感的设计和完整的任务管理功能。

## 🎨 界面特性

### 设计风格
- **未来科技风**: 深色主题 + 霓虹色彩
- **动态效果**: 流畅的动画和交互反馈
- **响应式布局**: 支持桌面和移动设备

### 核心功能
1. **任务控制面板**
   - 输入任务描述
   - 设置目标网站
   - 选择执行语言
   - 启动/停止任务

2. **实时监控**
   - 浏览器预览
   - 执行日志
   - 状态指示器

3. **统计面板**
   - 总执行步数
   - 任务成功率

## 📁 文件结构

```
frontend/
├── index.html              # 主界面
├── agent-controller.js     # 前端控制器
├── api_server.py          # Flask 后端 API
└── FRONTEND_GUIDE.md      # 本文档
```

## 🚀 快速开始

### 方式 1: 完整部署(推荐)

**步骤 1: 安装依赖**
```bash
pip install flask flask-cors
```

**步骤 2: 启动后端服务器**
```bash
python api_server.py
```

服务器将在 `http://localhost:5000` 启动

**步骤 3: 打开前端界面**
```bash
# 直接在浏览器中打开
open index.html

# 或使用简单的 HTTP 服务器
python -m http.server 8080
# 然后访问 http://localhost:8080
```

### 方式 2: 仅前端演示(Mock 模式)

如果后端未启动，前端会自动切换到 Mock 模式，使用模拟数据演示功能。

```bash
# 直接打开 HTML 文件
open index.html
```

## 🔌 集成你的 Agent

### 修改 `api_server.py`

在 `TaskExecutor._execute()` 方法中集成你的 Agent 代码:

```python
def _execute(self):
    try:
        self.status = 'running'
        self._update_task_status()
        
        # 导入你的模块
        from orchestrator import Orchestrator
        
        # 初始化
        orchestrator = Orchestrator()
        
        # 设置日志回调
        def log_callback(message, level='info', **kwargs):
            self.add_log(message, level, **kwargs)
        
        # 如果你的 Orchestrator 支持回调
        orchestrator.set_log_callback(log_callback)
        
        # 运行任务
        result = orchestrator.run(
            task_text=self.task_data['task_text'],
            constraints=self.task_data['constraints']
        )
        
        # 更新状态
        self.status = 'completed' if result['success'] else 'failed'
        self._update_task_status()
        
    except Exception as e:
        self.status = 'failed'
        self.add_log(f'执行失败: {str(e)}', 'error')
        self._update_task_status()
```

### 添加截图功能

```python
# 在任务执行后保存截图
from browser_module import BrowserObserver

observer = BrowserObserver()
screenshot = observer.take_screenshot()

screenshot_dir = './screenshots'
os.makedirs(screenshot_dir, exist_ok=True)
screenshot_path = f'{screenshot_dir}/{self.task_id}.png'

screenshot.save(screenshot_path)
self.screenshot_path = screenshot_path
self._update_task_status()
```

### 实时日志更新

```python
# 在 Orchestrator 循环中
while not is_done:
    # ... Agent 决策和执行 ...
    
    # 添加日志
    log_callback(f'步骤 {step_count}: {action_description}', 'info')
    
    # 更新截图
    if step_count % 3 == 0:  # 每3步更新一次截图
        # 保存并更新截图路径
        pass
```

## 🎯 API 接口说明

### 1. 健康检查
```http
GET /api/health

Response:
{
  "status": "healthy",
  "timestamp": "2026-02-05T12:00:00",
  "active_tasks": 2
}
```

### 2. 启动任务
```http
POST /api/task/start

Request Body:
{
  "task_text": "在谷歌搜索今天的美元汇率",
  "constraints": {
    "site": "google.com",
    "language": "zh-CN",
    "done_criteria": null
  }
}

Response:
{
  "task_id": "123e4567-e89b-12d3-a456-426614174000",
  "message": "任务已启动",
  "status": "pending"
}
```

### 3. 查询任务状态
```http
GET /api/task/status/{task_id}

Response:
{
  "task_id": "...",
  "task_text": "...",
  "status": "running",  // pending/running/completed/failed/stopped
  "logs": [
    {
      "timestamp": "2026-02-05T12:00:00",
      "message": "步骤 1: 初始化浏览器",
      "level": "info",
      "step": 1
    }
  ],
  "screenshot_url": "/api/screenshot/...",
  "created_at": "2026-02-05T12:00:00",
  "updated_at": "2026-02-05T12:00:05"
}
```

### 4. 停止任务
```http
POST /api/task/stop

Request Body:
{
  "task_id": "123e4567-e89b-12d3-a456-426614174000"
}

Response:
{
  "message": "任务停止请求已发送",
  "task_id": "..."
}
```

### 5. 获取截图
```http
GET /api/screenshot/{task_id}

Response: PNG Image
```

### 6. 列出所有任务
```http
GET /api/tasks

Response:
{
  "tasks": [
    {
      "task_id": "...",
      "task_text": "...",
      "status": "completed",
      "created_at": "..."
    }
  ]
}
```

## 🎨 自定义样式

### 修改配色方案

在 `index.html` 的 CSS 变量中修改:

```css
:root {
    /* 主色调 */
    --bg-primary: #0a0e17;
    --accent-cyan: #00f0ff;
    --accent-purple: #b84fff;
    
    /* 修改为你喜欢的颜色 */
    --accent-cyan: #ff6b6b;    /* 红色主题 */
    --accent-purple: #ffd93d;  /* 黄色主题 */
}
```

### 更换字体

```html
<!-- 在 <head> 中替换 Google Fonts 链接 -->
<link href="https://fonts.googleapis.com/css2?family=Your+Font&display=swap" rel="stylesheet">
```

```css
/* 在 CSS 中应用 */
body {
    font-family: 'Your Font', monospace;
}
```

## 🔧 高级配置

### 修改轮询间隔

在 `agent-controller.js` 中:

```javascript
startLogPolling() {
    this.logUpdateInterval = setInterval(() => {
        this.fetchTaskStatus();
    }, 1000);  // 改为 2000 表示每2秒更新一次
}
```

### 添加新的统计指标

**HTML (index.html):**
```html
<div class="stat-card">
    <div class="stat-value" id="avgTime">0s</div>
    <div class="stat-label">平均用时</div>
</div>
```

**JavaScript (agent-controller.js):**
```javascript
updateStats() {
    // ... 现有代码 ...
    
    // 计算平均用时
    const avgTime = this.stats.totalTasks > 0
        ? Math.round(this.stats.totalTime / this.stats.totalTasks)
        : 0;
    document.getElementById('avgTime').textContent = `${avgTime}s`;
}
```

## 📱 响应式设计

界面已针对以下设备优化:
- 桌面 (1920x1080+)
- 笔记本 (1366x768+)
- 平板 (768x1024)
- 手机 (375x667+)

## 🐛 故障排查

### 问题 1: 后端连接失败

**症状**: 控制台显示 "⚠ 后端未启动，使用模拟模式"

**解决方案**:
1. 确认后端服务器已启动: `python api_server.py`
2. 检查端口是否被占用: `lsof -i :5000`
3. 检查防火墙设置

### 问题 2: CORS 错误

**症状**: 浏览器控制台显示 CORS 相关错误

**解决方案**:
```python
# 在 api_server.py 中确保已安装并启用 CORS
from flask_cors import CORS
CORS(app)
```

### 问题 3: 前端无法加载

**症状**: 页面空白或样式错误

**解决方案**:
1. 使用 HTTP 服务器而非直接打开 HTML 文件
2. 检查浏览器控制台的错误信息
3. 确保 JavaScript 文件路径正确

## 🚀 性能优化

### 1. 减少轮询频率
```javascript
// 降低轮询频率以减少服务器负载
this.logUpdateInterval = setInterval(() => {
    this.fetchTaskStatus();
}, 3000);  // 从 1秒 改为 3秒
```

### 2. 限制日志数量
```javascript
addLog(message, type = 'info') {
    // ... 现有代码 ...
    
    // 限制日志条目数量
    const maxLogs = 100;
    while (this.logPanel.children.length > maxLogs) {
        this.logPanel.removeChild(this.logPanel.firstChild);
    }
}
```

### 3. 压缩截图
```python
# 在保存截图前压缩
from PIL import Image

screenshot = screenshot.resize((800, 600), Image.LANCZOS)
screenshot.save(screenshot_path, optimize=True, quality=85)
```

## 📚 扩展功能建议

1. **任务历史**: 保存并显示历史任务记录
2. **配置预设**: 保存常用任务配置
3. **多任务并发**: 支持同时运行多个任务
4. **WebSocket**: 使用 WebSocket 替代轮询,实现真正的实时更新
5. **导出报告**: 导出任务执行报告(PDF/JSON)
6. **用户认证**: 添加登录系统和权限管理

## 📞 支持

如有问题或建议,请查看:
- 浏览器控制台 (F12) 查看错误信息
- 后端日志输出
- API 响应数据

---

**版本**: 1.0.0  
**最后更新**: 2026-02-05  
**作者**: Claude
