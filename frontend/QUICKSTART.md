# 🚀 快速开始 - 3 步启动你的 Web Agent

## 方式 1: 一键启动 ⚡ (推荐)

```bash
python start.py
```

就这么简单! 脚本会自动:
- ✅ 检查 Python 版本
- ✅ 安装必要依赖
- ✅ 启动后端 API
- ✅ 启动前端服务器
- ✅ 在浏览器中打开界面

---

## 方式 2: 手动启动 🛠️

### 步骤 1: 安装依赖
```bash
pip install flask flask-cors
```

### 步骤 2: 启动后端
```bash
python api_server.py
```
看到这个输出表示成功:
```
Web Agent API Server
Server running at: http://localhost:5000
```

### 步骤 3: 打开前端
```bash
# 在新终端窗口运行
python -m http.server 8080
```

然后在浏览器访问: **http://localhost:8080/index.html**

---

## 方式 3: 仅查看界面 👀

直接双击 `index.html` 文件

> ⚠️ 注意: 这种方式会启用 Mock 模式(模拟数据),无法连接真实后端

---

## ⚠️ 重要提示: 浏览器缓存问题

如果你之前打开过旧版本的前端，浏览器可能缓存了旧文件。

**解决方法**: 在浏览器中按 `Ctrl + Shift + R` (Windows/Linux) 或 `Cmd + Shift + R` (Mac) 强制刷新

**验证成功**: 你应该看到"**执行结果记录**"面板，而不是"浏览器预览"或"操作步骤记录"

更多解决方案请查看 `TROUBLESHOOTING.md`

---

## 📖 界面使用

1. **输入任务**: 在"任务指令"框中输入,例如:
   ```
   在谷歌搜索今天的美元汇率
   ```

2. **设置选项** (可选):
   - 目标网站: `https://www.google.com`
   - 语言: `简体中文`

3. **启动任务**: 点击"启动任务"按钮

4. **查看执行**: 
   - 左侧: 状态和统计
   - 右侧: 浏览器预览和日志

5. **停止任务**: 点击"停止执行"按钮

---

## 🔌 集成你的 Agent

编辑 `api_server.py` 的第 88 行附近:

```python
def _execute(self):
    # 删除模拟代码,替换为:
    from orchestrator import Orchestrator  # 导入你的模块
    
    orchestrator = Orchestrator()
    result = orchestrator.run(
        task_text=self.task_data['task_text'],
        constraints=self.task_data['constraints']
    )
```

详细集成步骤请查看 `FRONTEND_GUIDE.md`

---

## 📁 文件说明

| 文件 | 用途 |
|------|------|
| `index.html` | 前端界面 |
| `agent-controller.js` | 前端逻辑 |
| `api_server.py` | 后端 API |
| `start.py` | 一键启动脚本 |
| `FRONTEND_GUIDE.md` | 详细使用指南 |
| `FRONTEND_README.md` | 项目总览 |

---

## ❓ 常见问题

**Q: 端口被占用怎么办?**
```bash
# 查看占用
lsof -i :5000

# 或者修改 api_server.py 最后一行的端口号
app.run(port=5001)  # 改为其他端口
```

**Q: 显示 CORS 错误?**
```bash
# 确保安装了 flask-cors
pip install flask-cors
```

**Q: 界面显示异常?**
- 使用 HTTP 服务器而非直接打开文件
- 检查浏览器控制台错误 (F12)

---

## 📚 进阶阅读

- **FRONTEND_GUIDE.md** - API 文档、自定义主题、故障排除
- **FRONTEND_README.md** - 架构设计、技术栈、扩展建议

---

## ✨ 快速测试

想看看界面长什么样? 最快的方式:

```bash
# 1. 启动后端 (新终端)
python api_server.py

# 2. 打开前端 (新终端)  
python -m http.server 8080

# 3. 在浏览器访问
open http://localhost:8080/index.html
```

或者一条命令:
```bash
python start.py
```

---

**祝你使用愉快! 🎉**

有问题? 查看 `FRONTEND_GUIDE.md` 或检查浏览器控制台 (F12)
