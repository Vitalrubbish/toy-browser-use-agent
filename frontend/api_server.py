"""
Web Agent Backend API Server
提供 RESTful API 供前端调用，控制 Agent 执行
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import threading
import uuid
import time
import os
from datetime import datetime
from typing import Dict, Any, List
import json
import asyncio
import sys

# 添加项目根目录到 sys.path 以便导入 browser_use
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv
    load_dotenv()
    from browser_use import Agent, ChatBrowserUse
except ImportError:
    print("Warning: Could not import browser_use. Ensure dependencies are installed.")

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 任务存储
tasks: Dict[str, Dict[str, Any]] = {}
task_lock = threading.Lock()


class TaskExecutor:
    """任务执行器 - 在独立线程中运行 Agent"""
    
    def __init__(self, task_id: str, task_data: Dict[str, Any]):
        self.task_id = task_id
        self.task_data = task_data
        self.logs: List[Dict[str, Any]] = []
        self.status = 'pending'
        self.screenshot_path = None
        self.thread = None
        
    def start(self):
        """启动任务执行线程"""
        self.thread = threading.Thread(target=self._execute, daemon=True)
        self.thread.start()
    
    def _execute(self):
        """执行任务（在独立线程中）"""
        try:
            self.status = 'running'
            self._update_task_status()
            
            # 创建新的事件循环运行异步 Agent
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def run_agent_task():
                self.add_log(f'正在初始化 Agent...', 'info')
                
                # 初始化 LLM (使用推荐的 ChatBrowserUse)
                # 注意：确保 .env 文件中设置了 BROWSER_USE_API_KEY
                llm = ChatBrowserUse()
                
                # 创建 Agent
                agent = Agent(
                    task=self.task_data['task_text'],
                    llm=llm,
                    use_memory=True,
                )
                
                self.add_log(f'开始执行任务: {self.task_data["task_text"]}', 'info')
                
                # 运行 Agent
                history = await agent.run()
                
                # 处理结果
                final_result = history.final_result()
                if final_result:
                    self.add_log(f'任务完成，结果: {final_result}', 'success')
                else:
                    self.add_log('任务完成', 'success')

                # 保存最后一个截图(如果有)
                screenshot_paths = history.screenshot_paths()
                if screenshot_paths:
                    last_screenshot = screenshot_paths[-1]
                    # 复制或链接到 frontend/screenshots 目录
                    screenshot_dir = os.path.join(os.path.dirname(__file__), 'screenshots')
                    os.makedirs(screenshot_dir, exist_ok=True)
                    target_path = os.path.join(screenshot_dir, f'{self.task_id}.png')
                    
                    # 简单复制文件
                    import shutil
                    shutil.copy2(last_screenshot, target_path)
                    
                    self.screenshot_path = target_path
                    self.add_log(f'截图已保存', 'info')
                
                return history

            # 运行异步任务
            loop.run_until_complete(run_agent_task())
            loop.close()
            
            self.status = 'completed'
            self._update_task_status()
            
        except Exception as e:
            self.status = 'failed'
            self.add_log(f'执行失败: {str(e)}', 'error')
            self._update_task_status()
    
    def _simulate_execution(self):
        """模拟执行（实际使用时替换为真实的 Agent 调用）"""
        steps = [
            {'step': 1, 'action': '初始化浏览器', 'delay': 1},
            {'step': 2, 'action': '导航到目标网站', 'delay': 1.5},
            {'step': 3, 'action': '观察页面状态', 'delay': 1},
            {'step': 4, 'action': '执行用户任务', 'delay': 2},
            {'step': 5, 'action': '验证结果', 'delay': 1},
        ]
        
        for step_data in steps:
            if self.status == 'stopped':
                break
                
            time.sleep(step_data['delay'])
            self.add_log(
                f"步骤 {step_data['step']}: {step_data['action']}",
                'info',
                step=step_data['step']
            )
    
    def add_log(self, message: str, level: str = 'info', **kwargs):
        """添加日志条目"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'level': level,
            **kwargs
        }
        self.logs.append(log_entry)
        self._update_task_status()
    
    def _update_task_status(self):
        """更新任务状态到全局存储"""
        with task_lock:
            tasks[self.task_id].update({
                'status': self.status,
                'logs': self.logs,
                'screenshot_url': self.screenshot_path,
                'updated_at': datetime.now().isoformat()
            })
    
    def stop(self):
        """停止任务执行"""
        self.status = 'stopped'
        self.add_log('任务被用户停止', 'warning')


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'active_tasks': len([t for t in tasks.values() if t['status'] == 'running'])
    })


@app.route('/api/task/start', methods=['POST'])
def start_task():
    """启动新任务"""
    try:
        data = request.json
        
        # 验证必需字段
        if 'task_text' not in data:
            return jsonify({'error': '缺少 task_text 字段'}), 400
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 创建任务记录
        task_data = {
            'task_id': task_id,
            'task_text': data['task_text'],
            'constraints': data.get('constraints', {}),
            'status': 'pending',
            'logs': [],
            'screenshot_url': None,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        with task_lock:
            tasks[task_id] = task_data
        
        # 启动任务执行器
        executor = TaskExecutor(task_id, data)
        executor.start()
        
        return jsonify({
            'task_id': task_id,
            'message': '任务已启动',
            'status': 'pending'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/task/status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """获取任务状态"""
    with task_lock:
        if task_id not in tasks:
            return jsonify({'error': '任务不存在'}), 404
        
        task = tasks[task_id].copy()
    
    return jsonify(task), 200


@app.route('/api/task/stop', methods=['POST'])
def stop_task():
    """停止任务执行"""
    try:
        data = request.json
        task_id = data.get('task_id')
        
        if not task_id:
            return jsonify({'error': '缺少 task_id'}), 400
        
        with task_lock:
            if task_id not in tasks:
                return jsonify({'error': '任务不存在'}), 404
            
            tasks[task_id]['status'] = 'stopped'
        
        return jsonify({
            'message': '任务停止请求已发送',
            'task_id': task_id
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/tasks', methods=['GET'])
def list_tasks():
    """列出所有任务"""
    with task_lock:
        task_list = [
            {
                'task_id': task_id,
                'task_text': task['task_text'],
                'status': task['status'],
                'created_at': task['created_at']
            }
            for task_id, task in tasks.items()
        ]
    
    return jsonify({'tasks': task_list}), 200


@app.route('/api/task/logs/<task_id>', methods=['GET'])
def get_task_logs(task_id):
    """获取任务日志"""
    with task_lock:
        if task_id not in tasks:
            return jsonify({'error': '任务不存在'}), 404
        
        logs = tasks[task_id]['logs']
    
    return jsonify({'logs': logs}), 200


@app.route('/api/screenshot/<task_id>', methods=['GET'])
def get_screenshot(task_id):
    """获取任务截图"""
    with task_lock:
        if task_id not in tasks:
            return jsonify({'error': '任务不存在'}), 404
        
        screenshot_path = tasks[task_id].get('screenshot_url')
    
    if not screenshot_path or not os.path.exists(screenshot_path):
        return jsonify({'error': '截图不存在'}), 404
    
    return send_file(screenshot_path, mimetype='image/png')


# === 集成你的 Agent 模块 ===

def integrate_real_agent():
    """
    将真实的 Agent 集成到 API 中
    
    步骤：
    1. 导入你的 Orchestrator 和相关模块
    2. 修改 TaskExecutor._execute() 方法
    3. 添加截图保存逻辑
    4. 添加实时日志回调
    """
    
    # 示例集成代码（取消注释并修改）:
    """
    from orchestrator import Orchestrator
    from browser_module import BrowserObserver, BrowserExecutor
    from agent_module import Agent
    from memory_retrieval import MemoryRetrieval
    
    class RealTaskExecutor(TaskExecutor):
        def _execute(self):
            try:
                self.status = 'running'
                self._update_task_status()
                
                # 初始化模块
                orchestrator = Orchestrator()
                
                # 设置日志回调
                def log_callback(message, level='info'):
                    self.add_log(message, level)
                
                orchestrator.set_log_callback(log_callback)
                
                # 运行任务
                result = orchestrator.run(
                    task_text=self.task_data['task_text'],
                    constraints=self.task_data['constraints']
                )
                
                # 保存最终截图
                if result.get('screenshot'):
                    screenshot_dir = './screenshots'
                    os.makedirs(screenshot_dir, exist_ok=True)
                    screenshot_path = f'{screenshot_dir}/{self.task_id}.png'
                    result['screenshot'].save(screenshot_path)
                    self.screenshot_path = screenshot_path
                
                self.status = 'completed' if result['success'] else 'failed'
                self._update_task_status()
                
            except Exception as e:
                self.status = 'failed'
                self.add_log(f'执行失败: {str(e)}', 'error')
                self._update_task_status()
    """
    pass


if __name__ == '__main__':
    print('=' * 60)
    print('Web Agent API Server')
    print('=' * 60)
    print(f'Server running at: http://localhost:5000')
    print(f'Health check: http://localhost:5000/api/health')
    print(f'Frontend: Open index.html in browser')
    print('=' * 60)
    
    # 开发模式：自动重载，显示调试信息
    port = int(os.environ.get('FLASK_PORT', 5000))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=True,
        threaded=True
    )
