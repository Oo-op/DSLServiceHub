class ChatInterface {
    constructor() {
        // 获取DOM元素：聊天消息区域、输入框和发送按钮
        this.chatMessages = document.getElementById('chatMessages');
        this.userInput = document.getElementById('userInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.sessionId = null; // 存储会话ID
        this.silenceTimer = null; // 静默检测定时器
        this.isWaiting = false;
        this.init();
    }
    
    init() {
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });
        
        document.querySelectorAll('.quick-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const message = e.target.getAttribute('data-message');
                this.userInput.value = message;
                this.sendMessage();
            });
        });
        
        this.startConversation();
    }
    
    // --- 静默计时器逻辑 ---
    handleSilenceTimer(timeout) {
        // 先清除旧的定时器
        if (this.silenceTimer) {
            clearTimeout(this.silenceTimer);
            this.silenceTimer = null;
        }

        // 如果后端返回了有效的超时时间 (毫秒)
        if (timeout && timeout > 0) {
            console.log(`启动静默检测: ${timeout}ms`);
            this.silenceTimer = setTimeout(() => {
                console.log("静默超时，自动发送空消息...");
                this.sendMessage(true); // true 表示这是系统自动触发的静默消息
            }, timeout);
        }
    }

    async startConversation() {
        try {
            const response = await fetch('/api/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await response.json();
            
            if (data.session_id) {
                this.sessionId = data.session_id;
            }
            
            this.addBotMessage(data.message);
            // 处理可能的超时设置
            this.handleSilenceTimer(data.timeout);

        } catch (error) {
            console.error('启动失败:', error);
            this.addBotMessage('连接服务器失败。');
        }
    }
    
    async sendMessage(isSilenceTrigger = false) {
        // 如果是用户主动发，且当前正在等待回复，则阻止（防止重复提交）
        // 如果是静默触发，允许执行
        if (!isSilenceTrigger && this.isWaiting) return;
        
        let message = "";
        
        if (!isSilenceTrigger) {
            message = this.userInput.value.trim();
            if (!message) return; // 用户不能发空消息
            
            this.addUserMessage(message);
            this.userInput.value = '';
            
            // 用户主动操作了，必须清除之前的静默定时器
            if (this.silenceTimer) {
                clearTimeout(this.silenceTimer);
                this.silenceTimer = null;
            }
        }
        
        this.showTypingIndicator();
        
        try {
            const response = await fetch('/api/message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    message: message, 
                    session_id: this.sessionId 
                })
            });
            
            const data = await response.json();
            this.hideTypingIndicator();
            
            if (data.error) {
                this.addBotMessage(data.error);
                if (data.end) this.disableInput();
            } else {
                this.addBotMessage(data.message);
                if (data.end) {
                    this.disableInput();
                    // 对话结束，清除定时器
                    if (this.silenceTimer) clearTimeout(this.silenceTimer);
                } else {
                    // 对话继续，根据后端指令重置定时器
                    this.handleSilenceTimer(data.timeout);
                }
            }
        } catch (error) {
            console.error('发送失败:', error);
            this.hideTypingIndicator();
            this.addBotMessage('网络错误');
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
        if (!message) return;
        const messageEl = document.createElement('div');
        messageEl.className = 'message bot-message';
        
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
        if (!this.silenceTimer) { 
            // 只有在非静默自动触发的情况下才禁用按钮
            // 如果是静默触发，其实按钮已经是可用的状态，但这里保持一致性
            this.sendBtn.disabled = true; 
        }
        
        const indicator = document.createElement('div');
        indicator.className = 'message bot-message typing-indicator';
        indicator.id = 'typingIndicator';
        indicator.innerHTML = '...';
        this.chatMessages.appendChild(indicator);
        this.scrollToBottom();
    }
    
    hideTypingIndicator() {
        this.isWaiting = false;
        this.sendBtn.disabled = false;
        const indicator = document.getElementById('typingIndicator');
        if (indicator) indicator.remove();
    }
    
    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    
    disableInput() {
        this.userInput.disabled = true;
        this.sendBtn.disabled = true;
        document.querySelectorAll('.quick-btn').forEach(btn => btn.disabled = true);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new ChatInterface();
});