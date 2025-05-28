/**
 * HWAgent Frontend Application
 * Modern JavaScript app with WebSocket streaming support
 */

class HWAgentApp {
    constructor() {
        this.socket = null;
        this.sessionId = null;
        this.messageCount = 0;
        this.isConnected = false;
        this.streamingEnabled = true;
        this.autoScrollEnabled = true;
        this.currentMessage = null;
        
        // DOM elements
        this.elements = {};
        
        this.init();
    }
    
    /**
     * Initialize the application
     */
    init() {
        this.cacheElements();
        this.setupEventListeners();
        this.initializeWebSocket();
        this.loadTools();
        this.hideLoadingOverlay();
    }
    
    /**
     * Cache DOM elements for better performance
     */
    cacheElements() {
        this.elements = {
            // Status and connection
            connectionStatus: document.getElementById('connectionStatus'),
            statusDot: document.querySelector('.status-dot'),
            statusText: document.querySelector('.status-text'),
            
            // Chat
            chatMessages: document.getElementById('chatMessages'),
            messageInput: document.getElementById('messageInput'),
            sendButton: document.getElementById('sendButton'),
            typingIndicator: document.getElementById('typingIndicator'),
            
            // Sidebar
            toolsList: document.getElementById('toolsList'),
            sessionId: document.getElementById('sessionId'),
            messageCount: document.getElementById('messageCount'),
            sessionStatus: document.getElementById('sessionStatus'),
            
            // Settings
            streamingToggle: document.getElementById('streamingToggle'),
            autoScrollToggle: document.getElementById('autoScrollToggle'),
            
            // Actions
            clearContextBtn: document.getElementById('clearContextBtn'),
            exportChatBtn: document.getElementById('exportChatBtn'),
            
            // Modals and overlays
            loadingOverlay: document.getElementById('loadingOverlay'),
            errorModal: document.getElementById('errorModal'),
            errorMessage: document.getElementById('errorMessage'),
            errorModalClose: document.getElementById('errorModalClose'),
            errorModalOk: document.getElementById('errorModalOk')
        };
    }
    
    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Send button
        this.elements.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Message input
        this.elements.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Auto-resize textarea
        this.elements.messageInput.addEventListener('input', () => this.autoResizeTextarea());
        
        // Settings toggles
        this.elements.streamingToggle.addEventListener('change', (e) => {
            this.streamingEnabled = e.target.checked;
            this.updateSessionStatus();
        });
        
        this.elements.autoScrollToggle.addEventListener('change', (e) => {
            this.autoScrollEnabled = e.target.checked;
        });
        
        // Action buttons
        this.elements.clearContextBtn.addEventListener('click', () => this.clearContext());
        this.elements.exportChatBtn.addEventListener('click', () => this.exportChat());
        
        // Error modal
        this.elements.errorModalClose.addEventListener('click', () => this.hideErrorModal());
        this.elements.errorModalOk.addEventListener('click', () => this.hideErrorModal());
        
        // Click outside modal to close
        this.elements.errorModal.addEventListener('click', (e) => {
            if (e.target === this.elements.errorModal) {
                this.hideErrorModal();
            }
        });
    }
    
    /**
     * Initialize WebSocket connection
     */
    initializeWebSocket() {
        try {
            this.socket = io({
                transports: ['websocket', 'polling'],
                timeout: 20000,
                forceNew: true
            });
            
            this.setupSocketListeners();
        } catch (error) {
            console.error('Failed to initialize WebSocket:', error);
            this.showError('Failed to initialize connection');
        }
    }
    
    /**
     * Setup WebSocket event listeners
     */
    setupSocketListeners() {
        this.socket.on('connect', () => {
            console.log('WebSocket connected');
            this.isConnected = true;
            this.sessionId = this.socket.id;
            this.updateConnectionStatus(true);
            this.updateSessionInfo();
        });
        
        this.socket.on('disconnect', () => {
            console.log('WebSocket disconnected');
            this.isConnected = false;
            this.updateConnectionStatus(false);
            this.updateSessionStatus('Disconnected');
        });
        
        this.socket.on('connected', (data) => {
            console.log('Session established:', data.session_id);
            this.sessionId = data.session_id;
            this.updateSessionInfo();
        });
        
        this.socket.on('stream_start', (data) => {
            console.log('Stream started:', data);
            this.showTypingIndicator();
            this.updateSessionStatus('Processing...');
        });
        
        this.socket.on('stream_chunk', (data) => {
            if (data.type === 'content') {
                this.appendToCurrentMessage(data.content);
            }
        });
        
        this.socket.on('stream_complete', (data) => {
            console.log('Stream completed');
            this.hideTypingIndicator();
            this.addMessage('assistant', data.response);
            this.currentMessage = null;
            this.updateSessionStatus('Ready');
            this.messageCount++;
            this.updateSessionInfo();
        });
        
        this.socket.on('error', (data) => {
            console.error('Socket error:', data);
            this.hideTypingIndicator();
            this.showError(data.message || 'Unknown error occurred');
            this.updateSessionStatus('Error');
        });
        
        this.socket.on('context_cleared', (data) => {
            this.showNotification('Context cleared successfully', 'success');
            this.updateSessionStatus('Ready');
        });
        
        this.socket.on('context_summary', (data) => {
            this.showNotification('Context: ' + data.summary, 'info');
        });
        
        // Connection error handling
        this.socket.on('connect_error', (error) => {
            console.error('Connection error:', error);
            this.updateConnectionStatus(false);
            this.showError('Connection failed. Please check your network.');
        });
        
        this.socket.on('reconnect', (attemptNumber) => {
            console.log('Reconnected after', attemptNumber, 'attempts');
            this.updateConnectionStatus(true);
            this.showNotification('Reconnected successfully', 'success');
        });
        
        this.socket.on('reconnect_error', (error) => {
            console.error('Reconnection failed:', error);
            this.showError('Failed to reconnect. Please refresh the page.');
        });
    }
    
    /**
     * Send message to agent
     */
    sendMessage() {
        const message = this.elements.messageInput.value.trim();
        if (!message || !this.isConnected) return;
        
        // Add user message to chat
        this.addMessage('user', message);
        this.elements.messageInput.value = '';
        this.autoResizeTextarea();
        
        // Send to agent
        if (this.streamingEnabled) {
            this.socket.emit('send_message', { message });
        } else {
            this.sendNonStreamingMessage(message);
        }
        
        this.messageCount++;
        this.updateSessionInfo();
    }
    
    /**
     * Send non-streaming message via REST API
     */
    async sendNonStreamingMessage(message) {
        try {
            this.showTypingIndicator();
            this.updateSessionStatus('Processing...');
            
            const response = await fetch(`/api/sessions/${this.sessionId}/messages`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.addMessage('assistant', data.response);
            
        } catch (error) {
            console.error('Failed to send message:', error);
            this.showError('Failed to send message: ' + error.message);
        } finally {
            this.hideTypingIndicator();
            this.updateSessionStatus('Ready');
        }
    }
    
    /**
     * Add message to chat
     */
    addMessage(sender, content, timestamp = null) {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${sender} fade-in`;
        
        const avatarElement = document.createElement('div');
        avatarElement.className = 'message-avatar';
        avatarElement.innerHTML = sender === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
        
        const contentElement = document.createElement('div');
        contentElement.className = 'message-content';
        
        const textElement = document.createElement('div');
        textElement.className = 'message-text';
        
        // Process content with markdown if it's from assistant
        if (sender === 'assistant') {
            textElement.innerHTML = this.processMarkdown(content);
        } else {
            textElement.textContent = content;
        }
        
        const timeElement = document.createElement('div');
        timeElement.className = 'message-time';
        timeElement.textContent = timestamp || this.getCurrentTime();
        
        contentElement.appendChild(textElement);
        contentElement.appendChild(timeElement);
        messageElement.appendChild(avatarElement);
        messageElement.appendChild(contentElement);
        
        // Remove welcome message if it exists
        const welcomeMessage = this.elements.chatMessages.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
        
        this.elements.chatMessages.appendChild(messageElement);
        
        if (this.autoScrollEnabled) {
            this.scrollToBottom();
        }
        
        return messageElement;
    }
    
    /**
     * Append content to current streaming message
     */
    appendToCurrentMessage(content) {
        if (!this.currentMessage) {
            this.currentMessage = this.addMessage('assistant', '');
        }
        
        const textElement = this.currentMessage.querySelector('.message-text');
        const currentContent = textElement.textContent;
        const newContent = currentContent + content;
        
        // Update with markdown processing
        textElement.innerHTML = this.processMarkdown(newContent);
        
        if (this.autoScrollEnabled) {
            this.scrollToBottom();
        }
    }
    
    /**
     * Process markdown content
     */
    processMarkdown(content) {
        if (typeof marked !== 'undefined') {
            return marked.parse(content);
        }
        
        // Basic markdown processing if marked.js is not available
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
            .replace(/\n/g, '<br>');
    }
    
    /**
     * Show/hide typing indicator
     */
    showTypingIndicator() {
        this.elements.typingIndicator.classList.add('active');
        if (this.autoScrollEnabled) {
            this.scrollToBottom();
        }
    }
    
    hideTypingIndicator() {
        this.elements.typingIndicator.classList.remove('active');
    }
    
    /**
     * Update connection status
     */
    updateConnectionStatus(connected) {
        this.elements.statusDot.className = `status-dot ${connected ? 'online' : 'offline'}`;
        this.elements.statusText.textContent = connected ? 'Connected' : 'Disconnected';
    }
    
    /**
     * Update session information
     */
    updateSessionInfo() {
        if (this.sessionId) {
            this.elements.sessionId.textContent = this.sessionId.substring(0, 8) + '...';
        }
        this.elements.messageCount.textContent = this.messageCount;
        this.updateSessionStatus();
    }
    
    /**
     * Update session status
     */
    updateSessionStatus(status = null) {
        if (status) {
            this.elements.sessionStatus.textContent = status;
        } else {
            const streamingStatus = this.streamingEnabled ? 'Streaming' : 'Standard';
            this.elements.sessionStatus.textContent = this.isConnected ? `Ready (${streamingStatus})` : 'Disconnected';
        }
    }
    
    /**
     * Auto-resize textarea
     */
    autoResizeTextarea() {
        const textarea = this.elements.messageInput;
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px';
    }
    
    /**
     * Scroll to bottom of chat
     */
    scrollToBottom() {
        setTimeout(() => {
            this.elements.chatMessages.scrollTop = this.elements.chatMessages.scrollHeight;
        }, 100);
    }
    
    /**
     * Clear context
     */
    clearContext() {
        if (!this.isConnected) {
            this.showError('Not connected to server');
            return;
        }
        
        if (confirm('Are you sure you want to clear the conversation context?')) {
            this.socket.emit('clear_context');
            
            // Clear chat messages except welcome
            const messages = this.elements.chatMessages.querySelectorAll('.message');
            messages.forEach(message => message.remove());
            
            // Reset message count
            this.messageCount = 0;
            this.updateSessionInfo();
            
            // Show welcome message again
            this.showWelcomeMessage();
        }
    }
    
    /**
     * Show welcome message
     */
    showWelcomeMessage() {
        const welcomeHtml = `
            <div class="welcome-message">
                <div class="welcome-content">
                    <i class="fas fa-rocket"></i>
                    <h2>Welcome to HWAgent!</h2>
                    <p>I'm your AI technical assistant. I can help you with:</p>
                    <ul>
                        <li>Mathematical calculations and computations</li>
                        <li>Code writing and debugging</li>
                        <li>Data analysis and processing</li>
                        <li>File operations and management</li>
                        <li>Web research and information gathering</li>
                        <li>Complex problem solving</li>
                    </ul>
                    <p>Just type your question or task below!</p>
                </div>
            </div>
        `;
        this.elements.chatMessages.innerHTML = welcomeHtml;
    }
    
    /**
     * Export chat history
     */
    exportChat() {
        const messages = Array.from(this.elements.chatMessages.querySelectorAll('.message'));
        const chatData = messages.map(message => {
            const sender = message.classList.contains('user') ? 'User' : 'Assistant';
            const content = message.querySelector('.message-text').textContent;
            const time = message.querySelector('.message-time').textContent;
            return { sender, content, time };
        });
        
        const exportData = {
            sessionId: this.sessionId,
            exportTime: new Date().toISOString(),
            messageCount: this.messageCount,
            messages: chatData
        };
        
        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `hwagent-chat-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        this.showNotification('Chat exported successfully', 'success');
    }
    
    /**
     * Load available tools
     */
    async loadTools() {
        try {
            const response = await fetch('/api/tools');
            if (!response.ok) {
                throw new Error('Failed to load tools');
            }
            
            const data = await response.json();
            this.displayTools(data.tools);
            
        } catch (error) {
            console.error('Failed to load tools:', error);
            this.elements.toolsList.innerHTML = '<div class="loading-tools">Failed to load tools</div>';
        }
    }
    
    /**
     * Display tools in sidebar
     */
    displayTools(tools) {
        if (!tools || tools.length === 0) {
            this.elements.toolsList.innerHTML = '<div class="loading-tools">No tools available</div>';
            return;
        }
        
        const toolsHtml = tools.map(tool => `
            <div class="tool-item">
                <div class="tool-name">${tool.name}</div>
                <div class="tool-description">${tool.description || 'No description available'}</div>
            </div>
        `).join('');
        
        this.elements.toolsList.innerHTML = toolsHtml;
    }
    
    /**
     * Show error modal
     */
    showError(message) {
        this.elements.errorMessage.textContent = message;
        this.elements.errorModal.classList.add('show');
    }
    
    /**
     * Hide error modal
     */
    hideErrorModal() {
        this.elements.errorModal.classList.remove('show');
    }
    
    /**
     * Show notification
     */
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--surface-color);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            padding: 1rem 1.5rem;
            box-shadow: var(--shadow-lg);
            z-index: 10001;
            max-width: 400px;
            transform: translateX(100%);
            transition: transform 0.3s ease;
        `;
        
        // Set color based on type
        const colors = {
            success: 'var(--success-color)',
            error: 'var(--error-color)',
            warning: 'var(--warning-color)',
            info: 'var(--primary-color)'
        };
        notification.style.borderLeftColor = colors[type] || colors.info;
        notification.style.borderLeftWidth = '4px';
        
        notification.textContent = message;
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);
        
        // Remove after delay
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
    
    /**
     * Hide loading overlay
     */
    hideLoadingOverlay() {
        setTimeout(() => {
            this.elements.loadingOverlay.classList.add('hidden');
        }, 1000);
    }
    
    /**
     * Get current time string
     */
    getCurrentTime() {
        return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.hwagentApp = new HWAgentApp();
});

// Handle page visibility for connection management
document.addEventListener('visibilitychange', () => {
    if (window.hwagentApp && !document.hidden) {
        // Page became visible, check connection
        if (!window.hwagentApp.isConnected && window.hwagentApp.socket) {
            window.hwagentApp.socket.connect();
        }
    }
}); 