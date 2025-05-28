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
        this.isInitialized = false;
        
        // DOM elements
        this.elements = {};
        
        this.init();
    }
    
    /**
     * Initialize the application
     */
    async init() {
        this.cacheElements();
        this.setupEventListeners();
        
        // Initialize session first
        await this.initializeSession();
        
        // Then setup WebSocket
        this.initializeWebSocket();
        
        // Initialize TMP Explorer
        this.initializeTmpExplorer();
        
        // Load tools and hide loading
        await this.loadTools();
        this.hideLoadingOverlay();
        
        this.isInitialized = true;
    }
    
    /**
     * Cache DOM elements
     */
    cacheElements() {
        // Chat elements
        this.elements = {
            // Main containers
            chatMessages: document.getElementById('chatMessages'),
            messageInput: document.getElementById('messageInput'),
            sendButton: document.getElementById('sendButton'),
            
            // Sidebar elements
            sidebar: document.querySelector('.sidebar'),
            sidebarToggle: document.querySelector('.sidebar-toggle'),
            headerSidebarToggle: document.getElementById('headerSidebarToggle'),
            sidebarOverlay: document.getElementById('sidebarOverlay'),
            
            // Settings
            streamingToggle: document.getElementById('streamingToggle'),
            autoScrollToggle: document.getElementById('autoScrollToggle'),
            
            // Action buttons
            clearContextBtn: document.getElementById('clearContextBtn'),
            exportChatBtn: document.getElementById('exportChatBtn'),
            
            // UI elements
            loadingOverlay: document.getElementById('loadingOverlay'),
            typingIndicator: document.getElementById('typingIndicator'),
            
            // Session info
            sessionId: document.getElementById('sessionId'),
            messageCount: document.getElementById('messageCount'),
            sessionStatus: document.getElementById('sessionStatus'),
            connectionStatus: document.getElementById('connectionStatus'),
            connectionText: document.getElementById('connectionText'),
            
            // Error modal
            errorModal: document.getElementById('errorModal'),
            errorModalClose: document.getElementById('errorModalClose'),
            errorModalOk: document.getElementById('errorModalOk'),
            errorMessage: document.getElementById('errorMessage'),
            
            // TMP directory elements
            tmpFileList: document.getElementById('tmpFileList'),
            tmpCurrentPath: document.getElementById('tmpCurrentPath'),
            tmpUpBtn: document.getElementById('tmpUpBtn'),
            tmpRefreshBtn: document.getElementById('tmpRefreshBtn'),
            tmpClosePreviewBtn: document.getElementById('closePreviewBtn'),
            tmpFilePreview: document.getElementById('tmpFilePreview'),
            
            // Tools
            toolsList: document.getElementById('toolsList')
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
        
        // Error modal click outside to close
        this.elements.errorModal?.addEventListener('click', (e) => {
            if (e.target === this.elements.errorModal) {
                this.hideErrorModal();
            }
        });

        // TMP file buttons
        if (this.elements.tmpUpBtn) {
            this.elements.tmpUpBtn.addEventListener('click', () => this.navigateTmpUp());
        }
        if (this.elements.tmpClosePreviewBtn) {
            this.elements.tmpClosePreviewBtn.addEventListener('click', () => this.closeTmpFilePreview());
        }

        // Setup collapsible sections
        this.setupCollapsibleSections();
        
        // Setup sidebar resizer
        this.setupSidebarResizer();
        
        // Setup sidebar toggle functionality
        this.setupSidebarToggle();
    }
    
    /**
     * Initialize session via REST API
     */
    async initializeSession() {
        try {
            const response = await fetch('/api/sessions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`Failed to create session: ${response.status} ${response.statusText}`);
            }
            
            const data = await response.json();
            this.sessionId = data.session_id;
            
            console.log('Session created:', this.sessionId);
            this.updateSessionInfo();
            
        } catch (error) {
            console.error('Failed to initialize session:', error);
            this.showError('Failed to initialize session: ' + error.message);
        }
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
            this.updateConnectionStatus(true);
            this.updateSessionStatus();
        });
        
        this.socket.on('disconnect', () => {
            console.log('WebSocket disconnected');
            this.isConnected = false;
            this.updateConnectionStatus(false);
            this.updateSessionStatus('Disconnected');
        });
        
        this.socket.on('connected', (data) => {
            console.log('WebSocket session established:', data.session_id);
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
            this.showError('Connection failed. Please check if the server is running.');
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
        if (!message) return;
        
        if (!this.isInitialized) {
            this.showError('Application is still initializing. Please wait...');
            return;
        }
        
        // Add user message to chat
        this.addMessage('user', message);
        this.elements.messageInput.value = '';
        this.autoResizeTextarea();
        
        // Send to agent
        if (this.streamingEnabled && this.isConnected) {
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
        if (!this.sessionId) {
            this.showError('No active session. Please refresh the page.');
            return;
        }
        
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
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
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
     * Update connection status indicator
     */
    updateConnectionStatus(connected) {
        if (this.elements.connectionStatus) {
            this.elements.connectionStatus.className = `status-dot ${connected ? 'online' : 'offline'}`;
        }
        if (this.elements.connectionText) {
            this.elements.connectionText.textContent = connected ? 'Connected' : 'Disconnected';
        }
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
        if (!this.sessionId) {
            this.showError('No active session');
            return;
        }
        
        if (confirm('Are you sure you want to clear the conversation context?')) {
            if (this.isConnected && this.streamingEnabled) {
                this.socket.emit('clear_context');
            } else {
                this.clearContextREST();
            }
            
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
     * Clear context via REST API
     */
    async clearContextREST() {
        try {
            const response = await fetch(`/api/sessions/${this.sessionId}/context`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                this.showNotification('Context cleared successfully', 'success');
            } else {
                throw new Error('Failed to clear context');
            }
        } catch (error) {
            this.showError('Failed to clear context: ' + error.message);
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
        }, 1500);
    }
    
    /**
     * Get current time string
     */
    getCurrentTime() {
        return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    // TMP Directory Explorer Logic
    initializeTmpExplorer() {
        this.currentTmpPath = '';
        this.loadTmpFiles();
    }

    async loadTmpFiles(path = '') {
        if (!this.elements.tmpFileList) return;
        this.elements.tmpFileList.innerHTML = '<div class="loading-message">Loading files...</div>';
        try {
            const response = await fetch(`/api/fs/tmp/list?path=${encodeURIComponent(path)}`);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `Failed to list files: ${response.status}`);
            }
            const data = await response.json();
            this.currentTmpPath = path;
            this.updateTmpPathDisplay(path);
            this.displayTmpFiles(data.files, path);
            this.elements.tmpUpBtn.disabled = path === '';
        } catch (error) {
            console.error('Error loading TMP files:', error);
            this.elements.tmpFileList.innerHTML = `<div class="error-message">Error: ${error.message}</div>`;
            this.showError(`Failed to load files from TMP directory: ${error.message}`);
        }
    }

    updateTmpPathDisplay(path) {
        if (!this.elements.tmpCurrentPath) return;
        this.elements.tmpCurrentPath.textContent = path ? `/${path}` : '/';
        this.elements.tmpCurrentPath.title = path ? `/${path}` : '/';
    }

    displayTmpFiles(files, currentPath) {
        if (!this.elements.tmpFileList) return;
        this.elements.tmpFileList.innerHTML = ''; // Clear previous list

        if (files.length === 0) {
            this.elements.tmpFileList.innerHTML = '<div class="empty-message">Directory is empty.</div>';
            return;
        }

        files.sort((a, b) => {
            if (a.is_dir === b.is_dir) {
                return a.name.localeCompare(b.name);
            }
            return a.is_dir ? -1 : 1; // Directories first
        });

        files.forEach(file => {
            const item = document.createElement('div');
            item.className = 'file-item';
            item.title = file.name;

            const icon = document.createElement('i');
            icon.className = `fas ${file.is_dir ? 'fa-folder' : 'fa-file-alt'}`;

            const nameSpan = document.createElement('span');
            nameSpan.textContent = file.name;

            item.appendChild(icon);
            item.appendChild(nameSpan);

            if (file.is_dir) {
                item.addEventListener('click', () => this.loadTmpFiles(currentPath ? `${currentPath}/${file.name}` : file.name));
            } else {
                item.addEventListener('click', () => this.viewTmpFile(currentPath ? `${currentPath}/${file.name}` : file.name));
            }

            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'delete-file-btn';
            deleteBtn.innerHTML = '<i class="fas fa-trash-alt"></i>';
            deleteBtn.title = `Delete ${file.is_dir ? 'folder' : 'file'}`;
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation(); // Prevent triggering click on parent item
                if (confirm(`Are you sure you want to delete '${file.name}'?`)) {
                    this.deleteTmpFile(currentPath ? `${currentPath}/${file.name}` : file.name, file.is_dir);
                }
            });

            item.appendChild(deleteBtn);
            this.elements.tmpFileList.appendChild(item);
        });
    }

    async viewTmpFile(filePath) {
        if (!this.elements.tmpFilePreview || !this.elements.tmpPreviewFileName || !this.elements.tmpPreviewFileContent) return;
        this.elements.tmpPreviewFileName.textContent = 'Loading...';
        this.elements.tmpPreviewFileContent.innerHTML = ''; // Clear previous content
        this.elements.tmpFilePreview.classList.add('active');

        try {
            const response = await fetch(`/api/fs/tmp/get?path=${encodeURIComponent(filePath)}`);
            if (!response.ok) {
                let errorText = `Failed to get file: ${response.status}`;
                try {
                    const errorData = await response.json();
                    errorText = errorData.error || errorText;
                } catch (e) { /* Ignore if response is not JSON */ }
                throw new Error(errorText);
            }

            const contentType = response.headers.get('content-type');
            const fileName = filePath.split('/').pop();
            this.elements.tmpPreviewFileName.textContent = fileName;

            if (contentType && (contentType.startsWith('text/') || contentType.includes('json') || contentType.includes('javascript'))) {
                const textContent = await response.text();
                this.elements.tmpPreviewFileContent.textContent = textContent;
            } else {
                // For non-text files, provide a download/open link
                const openLink = document.createElement('a');
                openLink.href = `/api/fs/tmp/get?path=${encodeURIComponent(filePath)}`;
                openLink.textContent = `Open '${fileName}' in new tab`;
                openLink.target = '_blank';
                openLink.style.display = 'block';
                openLink.style.padding = '1rem';
                openLink.style.textAlign = 'center';
                this.elements.tmpPreviewFileContent.appendChild(openLink);
                if (contentType && contentType.startsWith('image/')){
                    const imgPreview = document.createElement('img');
                    imgPreview.src = `/api/fs/tmp/get?path=${encodeURIComponent(filePath)}`;
                    imgPreview.style.maxWidth = '100%';
                    imgPreview.style.maxHeight = '150px';
                    imgPreview.style.display = 'block';
                    imgPreview.style.margin = '0.5rem auto';
                    this.elements.tmpPreviewFileContent.appendChild(imgPreview);
                }
            }
        } catch (error) {
            console.error('Error viewing TMP file:', error);
            this.elements.tmpPreviewFileName.textContent = 'Error';
            this.elements.tmpPreviewFileContent.textContent = error.message;
            this.showError(`Failed to view file: ${error.message}`);
        }
    }

    async deleteTmpFile(filePath, isDir) {
        try {
            const response = await fetch(`/api/fs/tmp/delete?path=${encodeURIComponent(filePath)}`, {
                method: 'DELETE'
            });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `Failed to delete: ${response.status}`);
            }
            const data = await response.json();
            this.showNotification(data.message || 'Successfully deleted.', 'success');
            this.loadTmpFiles(this.currentTmpPath); // Refresh the list
            this.closeTmpFilePreview(); // Close preview if deleted file was open
        } catch (error) {
            console.error('Error deleting TMP file/folder:', error);
            this.showError(`Failed to delete: ${error.message}`);
        }
    }

    navigateTmpUp() {
        if (!this.currentTmpPath) return;
        const parentPath = this.currentTmpPath.substring(0, this.currentTmpPath.lastIndexOf('/'));
        this.loadTmpFiles(parentPath);
    }

    closeTmpFilePreview() {
        if (!this.elements.tmpFilePreview) return;
        this.elements.tmpFilePreview.classList.remove('active');
        this.elements.tmpPreviewFileName.textContent = '';
        this.elements.tmpPreviewFileContent.textContent = '';
    }

    /**
     * Setup collapsible sections functionality
     */
    setupCollapsibleSections() {
        const sectionHeaders = document.querySelectorAll('.section-header');
        
        sectionHeaders.forEach(header => {
            header.addEventListener('click', (e) => {
                e.preventDefault();
                const targetId = header.getAttribute('data-target');
                const section = header.closest('.collapsible-section');
                const content = document.getElementById(targetId);
                
                if (section && content) {
                    this.toggleSection(section, content);
                }
            });
        });

        // Load saved section states from localStorage
        this.loadSectionStates();
    }

    /**
     * Toggle section collapse/expand
     */
    toggleSection(section, content) {
        const isCollapsed = section.classList.contains('collapsed');
        
        if (isCollapsed) {
            // Expand
            section.classList.remove('collapsed');
            content.style.maxHeight = content.scrollHeight + 'px';
            
            // Remove maxHeight after transition to allow dynamic content
            setTimeout(() => {
                if (!section.classList.contains('collapsed')) {
                    content.style.maxHeight = 'none';
                }
            }, 300);
        } else {
            // Collapse
            content.style.maxHeight = content.scrollHeight + 'px';
            // Force reflow
            content.offsetHeight;
            content.style.maxHeight = '0';
            section.classList.add('collapsed');
        }

        // Save section state
        this.saveSectionState(section);
    }

    /**
     * Save section state to localStorage
     */
    saveSectionState(section) {
        const sectionId = section.querySelector('.section-header').getAttribute('data-target');
        const isCollapsed = section.classList.contains('collapsed');
        
        try {
            const savedStates = JSON.parse(localStorage.getItem('hwagent_section_states') || '{}');
            savedStates[sectionId] = isCollapsed;
            localStorage.setItem('hwagent_section_states', JSON.stringify(savedStates));
        } catch (error) {
            console.warn('Failed to save section state:', error);
        }
    }

    /**
     * Load section states from localStorage
     */
    loadSectionStates() {
        try {
            const savedStates = JSON.parse(localStorage.getItem('hwagent_section_states') || '{}');
            
            Object.entries(savedStates).forEach(([sectionId, isCollapsed]) => {
                const content = document.getElementById(sectionId);
                const section = content?.closest('.collapsible-section');
                
                if (section && content && isCollapsed) {
                    section.classList.add('collapsed');
                    content.style.maxHeight = '0';
                }
            });
        } catch (error) {
            console.warn('Failed to load section states:', error);
        }
    }

    /**
     * Setup sidebar resizer functionality
     */
    setupSidebarResizer() {
        const sidebar = this.elements.sidebar;
        const resizer = this.elements.sidebarResizer;
        const toggleBtn = this.elements.sidebarToggle;
        const container = this.elements.chatContainer;
        
        if (!sidebar || !resizer || !container) return;

        let isResizing = false;
        let startX, startWidth;

        // Resizer drag functionality
        resizer.addEventListener('mousedown', (e) => {
            isResizing = true;
            startX = e.clientX;
            startWidth = parseInt(window.getComputedStyle(sidebar).width, 10);
            document.addEventListener('mousemove', handleResize);
            document.addEventListener('mouseup', stopResize);
            document.body.style.cursor = 'col-resize';
            e.preventDefault();
        });

        const handleResize = (e) => {
            if (!isResizing) return;
            
            const width = startWidth + (e.clientX - startX);
            const minWidth = 280;
            const maxWidth = Math.min(600, window.innerWidth * 0.5);
            
            if (width >= minWidth && width <= maxWidth) {
                // Update sidebar width
                sidebar.style.width = width + 'px';
                document.documentElement.style.setProperty('--sidebar-width', width + 'px');
                
                // Update dependent elements positions
                this.updateLayoutPositions(width);
                
                // Save width to localStorage
                localStorage.setItem('sidebarWidth', width);
            }
        };

        const stopResize = () => {
            isResizing = false;
            document.removeEventListener('mousemove', handleResize);
            document.removeEventListener('mouseup', stopResize);
            document.body.style.cursor = '';
        };

        // Toggle button functionality
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => {
                const isCollapsed = sidebar.classList.contains('collapsed');
                
                if (isCollapsed) {
                    // Expand
                    sidebar.classList.remove('collapsed');
                    const savedWidth = localStorage.getItem('sidebarWidth') || '300';
                    const width = parseInt(savedWidth);
                    sidebar.style.width = width + 'px';
                    document.documentElement.style.setProperty('--sidebar-width', width + 'px');
                    this.updateLayoutPositions(width);
                    localStorage.setItem('sidebarCollapsed', 'false');
                } else {
                    // Collapse
                    sidebar.classList.add('collapsed');
                    document.documentElement.style.setProperty('--sidebar-width', '60px');
                    this.updateLayoutPositions(60);
                    localStorage.setItem('sidebarCollapsed', 'true');
                }
            });
        }

        // Load saved state
        const savedWidth = localStorage.getItem('sidebarWidth');
        const isCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
        
        if (isCollapsed) {
            sidebar.classList.add('collapsed');
            document.documentElement.style.setProperty('--sidebar-width', '60px');
            this.updateLayoutPositions(60);
        } else if (savedWidth) {
            const width = parseInt(savedWidth);
            sidebar.style.width = width + 'px';
            document.documentElement.style.setProperty('--sidebar-width', width + 'px');
            this.updateLayoutPositions(width);
        } else {
            // Default width
            document.documentElement.style.setProperty('--sidebar-width', '300px');
            this.updateLayoutPositions(300);
        }
    }

    /**
     * Update layout positions for all dependent elements
     */
    updateLayoutPositions(sidebarWidth) {
        const chatContainer = this.elements.chatContainer;
        const inputContainer = document.querySelector('.chat-input-container');
        const typingIndicator = document.querySelector('.typing-indicator');
        
        // Update chat container position
        if (chatContainer) {
            chatContainer.style.left = sidebarWidth + 'px';
        }
        
        // Update input container position
        if (inputContainer) {
            inputContainer.style.left = sidebarWidth + 'px';
        }
        
        // Update typing indicator position
        if (typingIndicator) {
            typingIndicator.style.left = sidebarWidth + 'px';
        }
    }

    // Setup sidebar toggle functionality
    setupSidebarToggle() {
        const toggleBtn = this.elements.sidebarToggle;
        const headerToggleBtn = this.elements.headerSidebarToggle;
        const sidebar = this.elements.sidebar;
        const overlay = this.elements.sidebarOverlay;
        
        if (!sidebar) return;

        // Check if we're on mobile
        const isMobile = () => window.innerWidth <= 768;

        // Function to toggle sidebar
        const toggleSidebar = () => {
            if (isMobile()) {
                // Mobile mode
                const isOpen = sidebar.classList.contains('mobile-open');
                if (isOpen) {
                    sidebar.classList.remove('mobile-open');
                    if (overlay) overlay.classList.remove('active');
                } else {
                    sidebar.classList.add('mobile-open');
                    if (overlay) overlay.classList.add('active');
                }
            } else {
                // Desktop mode
                const isCollapsed = sidebar.classList.contains('collapsed');
                
                if (isCollapsed) {
                    // Expand
                    sidebar.classList.remove('collapsed');
                    const savedWidth = localStorage.getItem('sidebarWidth') || '300';
                    const width = parseInt(savedWidth);
                    sidebar.style.width = width + 'px';
                    document.documentElement.style.setProperty('--sidebar-width', width + 'px');
                    this.updateLayoutPositions(width);
                    localStorage.setItem('sidebarCollapsed', 'false');
                } else {
                    // Collapse
                    sidebar.classList.add('collapsed');
                    document.documentElement.style.setProperty('--sidebar-width', '60px');
                    this.updateLayoutPositions(60);
                    localStorage.setItem('sidebarCollapsed', 'true');
                }
            }
        };

        // Function to close mobile sidebar
        const closeMobileSidebar = () => {
            if (isMobile()) {
                sidebar.classList.remove('mobile-open');
                if (overlay) overlay.classList.remove('active');
            }
        };

        // Add event listeners to both toggle buttons
        if (toggleBtn) {
            toggleBtn.addEventListener('click', toggleSidebar);
        }
        if (headerToggleBtn) {
            headerToggleBtn.addEventListener('click', toggleSidebar);
        }

        // Close sidebar when clicking overlay
        if (overlay) {
            overlay.addEventListener('click', closeMobileSidebar);
        }

        // Close mobile sidebar on window resize
        window.addEventListener('resize', () => {
            if (!isMobile()) {
                sidebar.classList.remove('mobile-open');
                if (overlay) overlay.classList.remove('active');
            }
        });

        // Load saved collapsed state (desktop only)
        if (!isMobile()) {
            const isCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
            if (isCollapsed) {
                sidebar.classList.add('collapsed');
                document.documentElement.style.setProperty('--sidebar-width', '60px');
                this.updateLayoutPositions(60);
            }
        }
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