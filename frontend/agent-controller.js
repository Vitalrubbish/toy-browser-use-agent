/**
 * Web Agent Frontend Controller - 执行结果记录版本
 * 版本: 2.0
 * 更新时间: 2026-02-06
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
        
        console.log('Agent Controller v2.0 - 执行结果记录版本已加载');
    }

    initElements() {
        this.startBtn = document.getElementById('startBtn');
        this.stopBtn = document.getElementById('stopBtn');
        this.taskInput = document.getElementById('taskInput');
        this.targetSite = document.getElementById('targetSite');
        this.language = document.getElementById('language');
        this.statusDot = document.getElementById('statusDot');
        this.statusText = document.getElementById('statusText');
        this.logPanel = document.getElementById('logPanel');
        this.resultsPanel = document.getElementById('resultsPanel');
        this.totalStepsEl = document.getElementById('totalSteps');
        this.successRateEl = document.getElementById('successRate');
    }

    attachEventListeners() {
        this.startBtn.addEventListener('click', () => this.startTask());
        this.stopBtn.addEventListener('click', () => this.stopTask());
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
                headers: { 'Content-Type': 'application/json' },
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
                headers: { 'Content-Type': 'application/json' },
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
                if (data.logs && data.logs.length > 0) {
                    const lastLog = data.logs[data.logs.length - 1];
                    if (lastLog.step) {
                        this.addLog(`步骤 ${lastLog.step}: ${lastLog.message}`, 'info');
                        
                        if (lastLog.result_data) {
                            this.addResultCard(lastLog.result_data);
                        }
                        
                        this.stats.totalSteps++;
                        this.updateStats();
                    }
                }
            }
        } catch (error) {
            console.error('Status fetch error:', error);
        }
    }

    addResultCard(resultData) {
        if (this.resultsPanel.querySelector('.results-placeholder')) {
            this.resultsPanel.innerHTML = '';
        }

        const resultCard = document.createElement('div');
        const statusClass = resultData.success ? 'success' : (resultData.error ? 'failed' : 'info');
        resultCard.className = `result-card ${statusClass}`;
        
        const statusText = resultData.success ? '成功' : (resultData.error ? '失败' : '信息');
        let resultContent = this.buildResultContent(resultData);
        
        resultCard.innerHTML = `
            <div class="result-header">
                <span class="result-step">步骤 ${resultData.step_number}</span>
                <span class="result-status ${statusClass}">${statusText}</span>
            </div>
            <div class="result-title">${resultData.title || '执行结果'}</div>
            <div class="result-content">
                ${resultContent}
            </div>
            ${resultData.metadata ? this.buildMetadata(resultData.metadata) : ''}
        `;

        this.resultsPanel.appendChild(resultCard);
        this.resultsPanel.scrollTop = this.resultsPanel.scrollHeight;
    }

    buildResultContent(resultData) {
        let html = '<div class="result-data">';
        
        if (resultData.extracted_data) {
            html += '<div class="result-data-row"><span class="label">提取数据:</span></div>';
            
            if (typeof resultData.extracted_data === 'object') {
                for (let [key, value] of Object.entries(resultData.extracted_data)) {
                    html += '<div class="result-data-row">';
                    html += `<span class="label">  ${key}:</span>`;
                    html += `<span class="value">${this.escapeHtml(String(value))}</span>`;
                    html += '</div>';
                }
            } else {
                html += `<div class="result-data-row"><span class="value">${this.escapeHtml(String(resultData.extracted_data))}</span></div>`;
            }
        }
        
        if (resultData.page_info) {
            const info = resultData.page_info;
            html += '<div class="result-data-row"><span class="label">页面信息:</span></div>';
            
            if (info.title) {
                html += `<div class="result-data-row"><span class="label">  标题:</span><span class="value">${this.escapeHtml(info.title)}</span></div>`;
            }
            if (info.url) {
                html += `<div class="result-data-row"><span class="label">  URL:</span><span class="value highlight">${this.escapeHtml(info.url)}</span></div>`;
            }
            if (info.elements_count !== undefined) {
                html += `<div class="result-data-row"><span class="label">  元素数量:</span><span class="value">${info.elements_count}</span></div>`;
            }
        }
        
        if (resultData.action_result) {
            html += `<div class="result-data-row"><span class="label">操作结果:</span><span class="value">${this.escapeHtml(resultData.action_result)}</span></div>`;
        }
        
        if (resultData.found_elements) {
            html += '<div class="result-data-row"><span class="label">找到元素:</span></div>';
            html += '<table class="result-table"><tr><th>ID</th><th>类型</th><th>标签</th></tr>';
            resultData.found_elements.slice(0, 5).forEach(elem => {
                html += `<tr><td>${elem.id}</td><td>${elem.type}</td><td>${this.escapeHtml(elem.label || '-')}</td></tr>`;
            });
            html += '</table>';
            
            if (resultData.found_elements.length > 5) {
                html += `<div class="result-data-row" style="margin-top: 0.5rem;"><span class="label">... 还有 ${resultData.found_elements.length - 5} 个元素</span></div>`;
            }
        }
        
        if (resultData.error) {
            html += `<div class="result-data-row"><span class="label">错误:</span><span class="value" style="color: var(--accent-orange);">${this.escapeHtml(resultData.error)}</span></div>`;
        }
        
        if (resultData.message) {
            html += `<div class="result-data-row"><span class="value">${this.escapeHtml(resultData.message)}</span></div>`;
        }
        
        html += '</div>';
        return html;
    }

    buildMetadata(metadata) {
        let html = '<div class="result-metadata">';
        
        if (metadata.duration) {
            html += `<span><svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>${metadata.duration}ms</span>`;
        }
        
        if (metadata.url) {
            try {
                const hostname = new URL(metadata.url).hostname;
                html += `<span><svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>${hostname}</span>`;
            } catch (e) {
                html += `<span>${metadata.url}</span>`;
            }
        }
        
        if (metadata.timestamp) {
            const time = new Date(metadata.timestamp).toLocaleTimeString('zh-CN');
            html += `<span><svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>${time}</span>`;
        }
        
        html += '</div>';
        return html;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    addLog(message, type = 'info') {
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${type}`;
        
        const timestamp = new Date().toLocaleTimeString('zh-CN', { hour12: false });
        logEntry.innerHTML = `<span class="log-timestamp">[${timestamp}]</span><span>${message}</span>`;

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

    enableMockMode() {
        console.log('Mock mode enabled');
        this.apiBaseUrl = null;

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

            this.simulateMockExecution();
        };
    }

    simulateMockExecution() {
        const steps = [
            { 
                delay: 1000, 
                msg: '导航到 Google', 
                type: 'info',
                result: {
                    step_number: 1,
                    title: '导航到搜索引擎',
                    success: true,
                    page_info: {
                        title: 'Google',
                        url: 'https://www.google.com',
                        elements_count: 45
                    },
                    metadata: {
                        duration: 850,
                        url: 'https://www.google.com',
                        timestamp: new Date().toISOString()
                    }
                }
            },
            { 
                delay: 2000, 
                msg: '观察页面元素', 
                type: 'info',
                result: {
                    step_number: 2,
                    title: '页面元素识别',
                    success: true,
                    found_elements: [
                        { id: 1, type: 'input', label: '搜索' },
                        { id: 2, type: 'button', label: 'Google 搜索' },
                        { id: 3, type: 'button', label: '手气不错' },
                        { id: 4, type: 'link', label: 'Gmail' },
                        { id: 5, type: 'link', label: '图片' }
                    ],
                    metadata: {
                        duration: 320,
                        url: 'https://www.google.com',
                        timestamp: new Date().toISOString()
                    }
                }
            },
            { 
                delay: 3000, 
                msg: '输入搜索内容', 
                type: 'info',
                result: {
                    step_number: 3,
                    title: '文本输入完成',
                    success: true,
                    action_result: '已在搜索框中输入 "美元汇率"',
                    metadata: {
                        duration: 230,
                        url: 'https://www.google.com',
                        timestamp: new Date().toISOString()
                    }
                }
            },
            { 
                delay: 4000, 
                msg: '点击搜索按钮', 
                type: 'info',
                result: {
                    step_number: 4,
                    title: '触发搜索',
                    success: true,
                    action_result: '成功点击搜索按钮，页面开始跳转',
                    metadata: {
                        duration: 95,
                        url: 'https://www.google.com',
                        timestamp: new Date().toISOString()
                    }
                }
            },
            { 
                delay: 5000, 
                msg: '等待搜索结果', 
                type: 'info',
                result: {
                    step_number: 5,
                    title: '搜索结果加载完成',
                    success: true,
                    page_info: {
                        title: '美元汇率 - Google 搜索',
                        url: 'https://www.google.com/search?q=美元汇率',
                        elements_count: 128
                    },
                    metadata: {
                        duration: 1200,
                        url: 'https://www.google.com/search?q=美元汇率',
                        timestamp: new Date().toISOString()
                    }
                }
            },
            { 
                delay: 6000, 
                msg: '提取汇率信息', 
                type: 'info',
                result: {
                    step_number: 6,
                    title: '汇率数据提取成功',
                    success: true,
                    extracted_data: {
                        '货币对': 'USD/CNY',
                        '汇率': '7.2456',
                        '涨跌': '+0.0123 (+0.17%)',
                        '更新时间': '2026-02-05 14:30:00 UTC'
                    },
                    metadata: {
                        duration: 450,
                        url: 'https://www.google.com/search?q=美元汇率',
                        timestamp: new Date().toISOString()
                    }
                }
            },
            { 
                delay: 7000, 
                msg: '✓ 任务成功完成', 
                type: 'success',
                result: null
            }
        ];

        steps.forEach((step, index) => {
            setTimeout(() => {
                this.addLog(step.msg, step.type);
                
                if (step.result) {
                    this.addResultCard(step.result);
                    this.stats.totalSteps++;
                    this.updateStats();
                }

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

document.addEventListener('DOMContentLoaded', () => {
    const controller = new AgentController();
    
    fetch('http://localhost:5000/api/health')
        .then(response => {
            if (!response.ok) throw new Error('Backend not available');
            controller.addLog('✓ 已连接到后端服务', 'success');
        })
        .catch(() => {
            controller.addLog('⚠ 后端未启动，使用模拟模式', 'warning');
            controller.enableMockMode();
        });

    window.agentController = controller;
});
