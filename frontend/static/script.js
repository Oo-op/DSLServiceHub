// 静态文件: static/script.js
class ChatInterface {
    constructor() {
        this.chatMessages = document.getElementById('chatMessages');
        this.userInput = document.getElementById('userInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.isWaiting = false;
        
        this.init();
    }
    
    init() {
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });
        
        // 快捷按钮事件
        document.querySelectorAll('.quick-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const message = e.target.getAttribute('data-message');
                this.userInput.value = message;
                this.sendMessage();
            });
        });
        
        // 开始对话
        this.startConversation();
    }
    
    async startConversation() {
        try {
            const response = await fetch('/api/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            const data = await response.json();
            this.addBotMessage(data.message);
        } catch (error) {
            console.error('启动对话失败:', error);
            this.addBotMessage('您好！欢迎使用故宫博物院智能客服。');
        }
    }
    
    async sendMessage() {
        const message = this.userInput.value.trim();
        if (!message || this.isWaiting) return;
        
        this.addUserMessage(message);
        this.userInput.value = '';
        this.showTypingIndicator();
        
        try {
            const response = await fetch('/api/message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message })
            });
            
            const data = await response.json();
            this.hideTypingIndicator();
            
            if (data.error) {
                this.addBotMessage('系统出现错误，请稍后重试。');
            } else if (data.end) {
                this.addBotMessage(data.message);
                this.disableInput();
            } else {
                this.addBotMessage(data.message);
            }
        } catch (error) {
            console.error('发送消息失败:', error);
            this.hideTypingIndicator();
            this.addBotMessage('网络连接失败，请检查网络后重试。');
        }
    }
    
    addUserMessage(message) {
        const messageEl = document.createElement('div');
        messageEl.className = 'message user-message';
        messageEl.textContent = message;
        this.chatMessages.appendChild(messageEl);
        this.scrollToBottom();
    }
    
    addBotMessage(message) {
        const messageEl = document.createElement('div');
        messageEl.className = 'message bot-message';
        
        // 处理换行
        const lines = message.split('\n');
        lines.forEach((line, index) => {
            if (index > 0) messageEl.appendChild(document.createElement('br'));
            messageEl.appendChild(document.createTextNode(line));
        });
        
        this.chatMessages.appendChild(messageEl);
        this.scrollToBottom();
    }
    
    showTypingIndicator() {
        this.isWaiting = true;
        this.sendBtn.disabled = true;
        
        const indicator = document.createElement('div');
        indicator.className = 'message bot-message typing-indicator';
        indicator.id = 'typingIndicator';
        indicator.innerHTML = '客服正在输入<span class="typing-dots"><span>.</span><span>.</span><span>.</span></span>';
        
        this.chatMessages.appendChild(indicator);
        this.scrollToBottom();
    }
    
    hideTypingIndicator() {
        this.isWaiting = false;
        this.sendBtn.disabled = false;
        
        const indicator = document.getElementById('typingIndicator');
        if (indicator) {
            indicator.remove();
        }
    }
    
    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    
    disableInput() {
        this.userInput.disabled = true;
        this.sendBtn.disabled = true;
        document.querySelectorAll('.quick-btn').forEach(btn => {
            btn.disabled = true;
        });
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    new ChatInterface();
});