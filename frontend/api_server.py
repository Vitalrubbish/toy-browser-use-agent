"""
Web Agent Backend API Server - 执行结果记录版本
版本: 2.0
更新时间: 2026-02-06
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import uuid
import time
from datetime import datetime
from typing import Dict, Any, List

app = Flask(__name__)
CORS(app)

tasks: Dict[str, Dict[str, Any]] = {}
task_lock = threading.Lock()


class TaskExecutor:
    """任务执行器 - 在独立线程中运行 Agent"""
    
    def __init__(self, task_id: str, task_data: Dict[str, Any]):
        self.task_id = task_id
        self.task_data = task_data
        self.logs: List[Dict[str, Any]] = []
        self.status = 'pending'
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
            
            # 模拟执行 - 实际使用时替换为真实的 Agent 调用
            self._simulate_execution()
            
            self.status = 'completed'
            self._update_task_status()
            
        except Exception as e:
            self.status = 'failed'
            self.add_log(f'执行失败: {str(e)}', 'error')
            self._update_task_status()
    
    def _simulate_execution(self):
        """模拟执行"""
        steps = [
            {
                'step': 1,
                'title': '导航到搜索引擎',
                'delay': 1,
                'success': True,
                'page_info': {
                    'title': 'Google',
                    'url': 'https://www.google.com',
                    'elements_count': 45
                },
                'metadata': {
                    'duration': 850,
                    'url': 'https://www.google.com'
                }
            },
            {
                'step': 2,
                'title': '页面元素识别',
                'delay': 1.5,
                'success': True,
                'found_elements': [
                    {'id': 1, 'type': 'input', 'label': '搜索'},
                    {'id': 2, 'type': 'button', 'label': 'Google 搜索'},
                    {'id': 3, 'type': 'button', 'label': '手气不错'},
                ],
                'metadata': {
                    'duration': 320,
                    'url': 'https://www.google.com'
                }
            },
            {
                'step': 3,
                'title': '文本输入完成',
                'delay': 1,
                'success': True,
                'action_result': '已在搜索框中输入查询内容',
                'metadata': {
                    'duration': 230,
                    'url': 'https://www.google.com'
                }
            },
            {
                'step': 4,
                'title': '触发搜索',
                'delay': 1,
                'success': True,
                'action_result': '成功点击搜索按钮，页面开始跳转',
                'metadata': {
                    'duration': 95,
                    'url': 'https://www.google.com'
                }
            },
            {
                'step': 5,
                'title': '搜索结果加载完成',
                'delay': 1.5,
                'success': True,
                'page_info': {
                    'title': '搜索结果 - Google',
                    'url': 'https://www.google.com/search',
                    'elements_count': 128
                },
                'metadata': {
                    'duration': 1200,
                    'url': 'https://www.google.com/search'
                }
            },
            {
                'step': 6,
                'title': '数据提取成功',
                'delay': 1,
                'success': True,
                'extracted_data': {
                    '目标信息': '已找到',
                    '数据质量': '良好',
                    '结果数量': '约 1,230,000 条'
                },
                'metadata': {
                    'duration': 450,
                    'url': 'https://www.google.com/search'
                }
            }
        ]
        
        for step_data in steps:
            if self.status == 'stopped':
                break
            
            time.sleep(step_data['delay'])
            
            result_kwargs = {k: v for k, v in step_data.items() 
                           if k not in ['step', 'title', 'delay']}
            
            self.add_result(
                step_number=step_data['step'],
                title=step_data['title'],
                **result_kwargs
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
    
    def add_result(self, step_number: int, title: str, **kwargs):
        """
        添加步骤执行结果
        
        Args:
            step_number: 步骤编号
            title: 结果标题
            **kwargs: 结果详细信息
                - success: 是否成功 (bool)
                - extracted_data: 提取的数据 (dict)
                - page_info: 页面信息 (dict)
                - action_result: 操作结果描述 (str)
                - found_elements: 找到的元素列表 (list)
                - error: 错误信息 (str)
                - message: 通用消息 (str)
                - metadata: 元数据 (dict)
        """
        result_data = {
            'step_number': step_number,
            'title': title,
            'timestamp': datetime.now().isoformat(),
            **kwargs
        }
        
        if 'metadata' not in result_data:
            result_data['metadata'] = {}
        if 'timestamp' not in result_data['metadata']:
            result_data['metadata']['timestamp'] = datetime.now().isoformat()
        
        self.add_log(
            title,
            'success' if kwargs.get('success', True) else 'error',
            step=step_number,
            result_data=result_data
        )
    
    def _update_task_status(self):
        """更新任务状态到全局存储"""
        with task_lock:
            tasks[self.task_id].update({
                'status': self.status,
                'logs': self.logs,
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
        'version': '2.0',
        'timestamp': datetime.now().isoformat(),
        'active_tasks': len([t for t in tasks.values() if t['status'] == 'running'])
    })


@app.route('/api/task/start', methods=['POST'])
def start_task():
    """启动新任务"""
    try:
        data = request.json
        
        if 'task_text' not in data:
            return jsonify({'error': '缺少 task_text 字段'}), 400
        
        task_id = str(uuid.uuid4())
        
        task_data = {
            'task_id': task_id,
            'task_text': data['task_text'],
            'constraints': data.get('constraints', {}),
            'status': 'pending',
            'logs': [],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        with task_lock:
            tasks[task_id] = task_data
        
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


# === 集成你的 Agent 模块 ===

def integrate_real_agent():
    """
    将真实的 Agent 集成到 API 中
    
    示例集成代码:
    """
    pass
    """
    from orchestrator import Orchestrator
    
    class RealTaskExecutor(TaskExecutor):
        def _execute(self):
            try:
                self.status = 'running'
                self._update_task_status()
                
                orchestrator = Orchestrator()
                step_count = 0
                
                while not orchestrator.is_done():
                    step_count += 1
                    
                    browser_state = orchestrator.browser_observer.observe()
                    action = orchestrator.agent.decide(
                        task_text=self.task_data['task_text'],
                        browser_state=browser_state
                    )
                    
                    start_time = time.time()
                    result = orchestrator.browser_executor.execute(action)
                    duration = int((time.time() - start_time) * 1000)
                    
                    # 记录执行结果
                    if action['type'] == 'navigate':
                        self.add_result(
                            step_number=step_count,
                            title=f'导航到 {action["url"]}',
                            success=result['success'],
                            page_info={
                                'url': action['url'],
                                'title': browser_state.get('title', ''),
                                'elements_count': len(browser_state.get('interactive_elements', []))
                            },
                            metadata={'duration': duration, 'url': action['url']}
                        )
                    
                    elif 'extracted_data' in result:
                        self.add_result(
                            step_number=step_count,
                            title='数据提取成功',
                            success=True,
                            extracted_data=result['extracted_data'],
                            metadata={'duration': duration, 'url': browser_state['url']}
                        )
                
                self.status = 'completed'
                self._update_task_status()
                
            except Exception as e:
                self.status = 'failed'
                self.add_log(f'执行失败: {str(e)}', 'error')
                self._update_task_status()
    """


if __name__ == '__main__':
    print('=' * 60)
    print('Web Agent API Server v2.0 - 执行结果记录版本')
    print('=' * 60)
    print(f'Server running at: http://localhost:5000')
    print(f'Health check: http://localhost:5000/api/health')
    print(f'Frontend: http://localhost:8080/index.html')
    print('=' * 60)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )
