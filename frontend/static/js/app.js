/**
 * MacMind Web 前端应用
 * Cyberpunk-styled AI Assistant Frontend
 */

class MacMindApp {
    constructor() {
        this.socket = null;
        this.chatWindow = document.getElementById('chat-window');
        this.messageInput = document.getElementById('message-input');
        this.sendBtn = document.getElementById('send-btn');
        this.clearBtn = document.getElementById('clear-btn');
        this.statusDot = document.getElementById('status-dot');
        this.statusText = document.getElementById('status-text');
        this.toolNotification = document.getElementById('tool-notification');
        this.toolText = document.getElementById('tool-text');
        
        this.isProcessing = false;
        
        this.init();
    }
    
    init() {
        this.setupMarkdown();
        this.connectWebSocket();
        this.attachEventListeners();
        this.clearWelcomeMessage();
    }
    
    setupMarkdown() {
        // 配置 marked 支持代码高亮
        marked.setOptions({
            highlight: function(code, lang) {
                if (lang && hljs.getLanguage(lang)) {
                    return hljs.highlight(code, { language: lang }).value;
                }
                return hljs.highlightAuto(code).value;
            },
            breaks: true,
            gfm: true
        });
    }
    
    connectWebSocket() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('WebSocket连接已建立');
            this.updateStatus('online', 'CONNECTED');
        });
        
        this.socket.on('disconnect', () => {
            console.log('WebSocket连接已断开');
            this.updateStatus('error', 'DISCONNECTED');
        });
        
        this.socket.on('connected', (data) => {
            console.log('服务器确认连接:', data);
        });
        
        this.socket.on('user_message', (data) => {
            this.appendMessage(data.message, 'user');
        });
        
        this.socket.on('ai_response', (data) => {
            this.appendMessage(data.message, 'ai');
            this.isProcessing = false;
            this.enableInput();
        });
        
        this.socket.on('tool_execution', (data) => {
            this.showToolNotification(`执行工具: ${data.function}`);
            this.appendToolMessage(`🔧 执行工具: ${data.function}`, 'executing');
        });
        
        this.socket.on('tool_result', (data) => {
            const status = data.success ? '✅' : '❌';
            const message = data.success 
                ? `${status} ${data.function} 执行成功` 
                : `${status} ${data.function} 执行失败: ${data.error}`;
            this.appendToolMessage(message, data.success ? 'success' : 'error');
            this.hideToolNotification();
        });
        
        this.socket.on('error', (data) => {
            this.appendMessage(`错误: ${data.error}`, 'error');
            this.isProcessing = false;
            this.enableInput();
            this.hideToolNotification();
        });
    }
    
    attachEventListeners() {
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        this.clearBtn.addEventListener('click', () => this.clearChat());
    }
    
    sendMessage() {
        const message = this.messageInput.value.trim();
        
        if (!message || this.isProcessing) {
            return;
        }
        
        this.isProcessing = true;
        this.disableInput();
        
        this.socket.emit('chat_message', { message });
        
        this.messageInput.value = '';
    }
    
    appendMessage(text, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message message-${type}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        if (type === 'user') {
            const label = document.createElement('div');
            label.className = 'message-label';
            label.textContent = 'USER';
            contentDiv.appendChild(label);
        } else if (type === 'ai') {
            const label = document.createElement('div');
            label.className = 'message-label';
            label.textContent = 'AI';
            contentDiv.appendChild(label);
        }
        
        const textDiv = document.createElement('div');
        textDiv.className = 'message-text';
        
        if (type === 'ai') {
            // AI 响应使用 Markdown 渲染
            textDiv.innerHTML = marked.parse(text);
            // 高亮所有代码块
            textDiv.querySelectorAll('pre code').forEach((block) => {
                hljs.highlightElement(block);
            });
        } else {
            // 用户消息保持纯文本但支持换行
            textDiv.textContent = text;
        }
        
        contentDiv.appendChild(textDiv);
        
        messageDiv.appendChild(contentDiv);
        this.chatWindow.appendChild(messageDiv);
        
        this.scrollToBottom();
    }
    
    appendToolMessage(text, status) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message message-tool';
        messageDiv.textContent = text;
        
        if (status === 'executing') {
            messageDiv.style.borderColor = 'var(--cyber-yellow)';
            messageDiv.style.color = 'var(--cyber-yellow)';
        } else if (status === 'success') {
            messageDiv.style.borderColor = 'var(--cyber-green)';
            messageDiv.style.color = 'var(--cyber-green)';
        } else if (status === 'error') {
            messageDiv.style.borderColor = 'var(--cyber-pink)';
            messageDiv.style.color = 'var(--cyber-pink)';
        }
        
        this.chatWindow.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    clearChat() {
        fetch('/api/clear', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.chatWindow.innerHTML = '';
                this.appendMessage('对话历史已清空', 'ai');
            }
        })
        .catch(error => {
            console.error('清空历史失败:', error);
        });
    }
    
    clearWelcomeMessage() {
        setTimeout(() => {
            const welcome = this.chatWindow.querySelector('.welcome-message');
            if (welcome && this.chatWindow.children.length > 1) {
                const glitchElement = welcome.querySelector('.glitch');
                if (glitchElement) {
                    glitchElement.style.animation = 'none';
                }
                welcome.style.opacity = '0';
                setTimeout(() => welcome.remove(), 300);
            }
        }, 3000);
    }
    
    updateStatus(type, text) {
        this.statusDot.className = `status-dot ${type}`;
        this.statusText.textContent = text;
    }
    
    showToolNotification(text) {
        this.toolText.textContent = text;
        this.toolNotification.classList.add('show');
    }
    
    hideToolNotification() {
        setTimeout(() => {
            this.toolNotification.classList.remove('show');
        }, 1000);
    }
    
    disableInput() {
        this.messageInput.disabled = true;
        this.sendBtn.disabled = true;
        this.sendBtn.style.opacity = '0.5';
    }
    
    enableInput() {
        this.messageInput.disabled = false;
        this.sendBtn.disabled = false;
        this.sendBtn.style.opacity = '1';
        this.messageInput.focus();
    }
    
    scrollToBottom() {
        this.chatWindow.scrollTop = this.chatWindow.scrollHeight;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const app = new MacMindApp();
    console.log('MacMind Web App 已启动');
});
