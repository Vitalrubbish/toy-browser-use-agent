/**
 * Web Agent Frontend Controller
 * 负责与后端 API 通信，控制 Agent 执行
 */

class AgentController {
    constructor() {
        this.apiBaseUrl = 'http://localhost:5000/api';
        this.isRunning = false;
        this.currentTaskId = null;
        this.logUpdateInterval = null;
        this.stats = {
            totalSteps: 0,
            successCount: 0,
            totalTasks: 0
        };

        this.initElements();
        this.attachEventListeners();
        this.loadStats();
    }

    initElements() {
        // Buttons
        this.startBtn = document.getElementById('startBtn');
        this.stopBtn = document.getElementById('stopBtn');

        // Inputs
        this.taskInput = document.getElementById('taskInput');
        this.targetSite = document.getElementById('targetSite');
        this.language = document.getElementById('language');

        // Status
        this.statusDot = document.getElementById('statusDot');
        this.statusText = document.getElementById('statusText');

        // Logs
        this.logPanel = document.getElementById('logPanel');

        // Preview
        this.browserPreview = document.getElementById('browserPreview');

        // Stats
        this.totalStepsEl = document.getElementById('totalSteps');
        this.successRateEl = document.getElementById('successRate');
    }

    attachEventListeners() {
        this.startBtn.addEventListener('click', () => this.startTask());
        this.stopBtn.addEventListener('click', () => this.stopTask());

        // Enter to submit
        this.taskInput.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                this.startTask();
            }
        });
    }

    async startTask() {
        const taskText = this.taskInput.value.trim();
        if (!taskText) {
            this.addLog('请输入任务描述', 'warning');
            return;
        }

        this.setStatus('running', '执行中...');
        this.startBtn.disabled = true;
        this.stopBtn.disabled = false;
        this.isRunning = true;

        const payload = {
            task_text: taskText,
            constraints: {
                site: this.targetSite.value || null,
                language: this.language.value,
                done_criteria: null
            }
        };

        this.addLog(`启动任务: ${taskText}`, 'info');

        try {
            const response = await fetch(`${this.apiBaseUrl}/task/start`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (response.ok) {
                this.currentTaskId = data.task_id;
                this.addLog(`任务ID: ${data.task_id}`, 'success');
                this.startLogPolling();
            } else {
                throw new Error(data.error || '任务启动失败');
            }
        } catch (error) {
            this.addLog(`错误: ${error.message}`, 'error');
            this.setStatus('error', '执行失败');
            this.resetControls();
        }
    }

    async stopTask() {
        if (!this.currentTaskId) return;

        this.addLog('正在停止任务...', 'warning');

        try {
            const response = await fetch(`${this.apiBaseUrl}/task/stop`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ task_id: this.currentTaskId })
            });

            const data = await response.json();
            this.addLog(data.message || '任务已停止', 'info');
        } catch (error) {
            this.addLog(`停止失败: ${error.message}`, 'error');
        }

        this.stopLogPolling();
        this.resetControls();
    }

    startLogPolling() {
        this.logUpdateInterval = setInterval(() => {
            this.fetchTaskStatus();
        }, 1000);
    }

    stopLogPolling() {
        if (this.logUpdateInterval) {
            clearInterval(this.logUpdateInterval);
            this.logUpdateInterval = null;
        }
    }

    async fetchTaskStatus() {
        if (!this.currentTaskId) return;

        try {
            const response = await fetch(`${this.apiBaseUrl}/task/status/${this.currentTaskId}`);
            const data = await response.json();

            if (data.status === 'completed') {
                this.addLog('✓ 任务完成', 'success');
                this.setStatus('idle', '任务完成');
                this.stopLogPolling();
                this.resetControls();
                this.stats.successCount++;
                this.stats.totalTasks++;
                this.updateStats();
            } else if (data.status === 'failed') {
                this.addLog('✗ 任务失败', 'error');
                this.setStatus('error', '执行失败');
                this.stopLogPolling();
                this.resetControls();
                this.stats.totalTasks++;
                this.updateStats();
            } else if (data.status === 'running') {
                // Update logs
                if (data.logs && data.logs.length > 0) {
                    const lastLog = data.logs[data.logs.length - 1];
                    if (lastLog.step) {
                        this.addLog(`步骤 ${lastLog.step}: ${lastLog.action}`, 'info');
                        this.stats.totalSteps++;
                        this.updateStats();
                    }
                }

                // Update screenshot if available
                if (data.screenshot_url) {
                    this.updateBrowserPreview(data.screenshot_url);
                }
            }
        } catch (error) {
            console.error('Status fetch error:', error);
        }
    }

    addLog(message, type = 'info') {
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${type}`;
        
        const timestamp = new Date().toLocaleTimeString('zh-CN', { hour12: false });
        logEntry.innerHTML = `
            <span class="log-timestamp">[${timestamp}]</span>
            <span>${message}</span>
        `;

        this.logPanel.appendChild(logEntry);
        this.logPanel.scrollTop = this.logPanel.scrollHeight;
    }

    setStatus(status, text) {
        this.statusDot.className = `status-dot ${status}`;
        this.statusText.textContent = text;
    }

    resetControls() {
        this.startBtn.disabled = false;
        this.stopBtn.disabled = true;
        this.isRunning = false;
        this.currentTaskId = null;
        this.setStatus('idle', '系统就绪');
    }

    updateBrowserPreview(screenshotUrl) {
        this.browserPreview.innerHTML = `
            <img src="${screenshotUrl}" 
                 alt="Browser Screenshot" 
                 style="width: 100%; height: auto; border-radius: 8px;"
            >
        `;
    }

    updateStats() {
        this.totalStepsEl.textContent = this.stats.totalSteps;
        
        const successRate = this.stats.totalTasks > 0 
            ? Math.round((this.stats.successCount / this.stats.totalTasks) * 100)
            : 0;
        this.successRateEl.textContent = `${successRate}%`;

        this.saveStats();
    }

    saveStats() {
        localStorage.setItem('agentStats', JSON.stringify(this.stats));
    }

    loadStats() {
        const saved = localStorage.getItem('agentStats');
        if (saved) {
            this.stats = JSON.parse(saved);
            this.updateStats();
        }
    }

    // Mock API for development (remove when backend is ready)
    enableMockMode() {
        console.log('Mock mode enabled - no backend required');
        this.apiBaseUrl = null;

        // Override API calls with mock responses
        this.startTask = async () => {
            const taskText = this.taskInput.value.trim();
            if (!taskText) {
                this.addLog('请输入任务描述', 'warning');
                return;
            }

            this.setStatus('running', '执行中...');
            this.startBtn.disabled = true;
            this.stopBtn.disabled = false;
            this.isRunning = true;

            this.currentTaskId = 'mock-' + Date.now();
            this.addLog(`启动任务: ${taskText}`, 'info');
            this.addLog(`任务ID: ${this.currentTaskId}`, 'success');

            // Simulate execution
            this.simulateMockExecution();
        };
    }

    simulateMockExecution() {
        const steps = [
            { delay: 1000, msg: '步骤 1: 打开浏览器', type: 'info' },
            { delay: 2000, msg: '步骤 2: 导航至目标网站', type: 'info' },
            { delay: 3000, msg: '步骤 3: 定位搜索框', type: 'info' },
            { delay: 4000, msg: '步骤 4: 输入搜索内容', type: 'info' },
            { delay: 5000, msg: '步骤 5: 点击搜索按钮', type: 'info' },
            { delay: 6000, msg: '步骤 6: 等待结果加载', type: 'info' },
            { delay: 7000, msg: '✓ 任务成功完成', type: 'success' }
        ];

        steps.forEach((step, index) => {
            setTimeout(() => {
                this.addLog(step.msg, step.type);
                this.stats.totalSteps++;
                this.updateStats();

                if (index === steps.length - 1) {
                    this.setStatus('idle', '任务完成');
                    this.resetControls();
                    this.stats.successCount++;
                    this.stats.totalTasks++;
                    this.updateStats();
                }
            }, step.delay);
        });
    }
}

// Initialize controller when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const controller = new AgentController();
    
    // Check if backend is available
    fetch('http://localhost:5000/api/health')
        .then(response => {
            if (!response.ok) throw new Error('Backend not available');
            controller.addLog('✓ 已连接到后端服务', 'success');
        })
        .catch(() => {
            controller.addLog('⚠ 后端未启动，使用模拟模式', 'warning');
            controller.enableMockMode();
        });

    // Make controller globally accessible for debugging
    window.agentController = controller;
});
