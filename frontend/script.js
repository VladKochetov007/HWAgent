document.addEventListener('DOMContentLoaded', () => {
    // Socket.IO connection
    const socket = io();
    
    // Elements
    const messageInput = document.getElementById('message-input');
    const sendButton = document.querySelector('.send-message');
    const fileButton = document.querySelector('.upload-file');
    const chatMessages = document.getElementById('chat-messages');
    const newChatButton = document.getElementById('new-chat');
    const modelSelect = document.getElementById('model-select');
    const apiKeyInput = document.querySelector('.api-input input');
    const themeToggle = document.getElementById('theme-toggle');

    // Chat state
    let currentChat = [];
    let isProcessing = false;
    let currentStreamingMessage = null;

    // Socket event handlers
    socket.on('connected', (data) => {
        console.log('Connected to server:', data.session_id);
        addSystemMessage('Connected to HWAgent server');
    });

    socket.on('disconnect', () => {
        console.log('Disconnected from server');
        addSystemMessage('Disconnected from server');
    });

    socket.on('error', (data) => {
        console.error('Error:', data.message);
        addSystemMessage(`Error: ${data.message}`, 'error');
        isProcessing = false;
        updateSendButton();
    });

    // Agent response events
    socket.on('user_message', (data) => {
        // User message already added, just log
        console.log('User message processed:', data.content);
    });

    socket.on('iteration_start', (data) => {
        addSystemMessage(`--- Agent Iteration ${data.iteration}/${data.max_iterations} ---`, 'iteration');
    });

    socket.on('thought', (data) => {
        addAgentSection('thought', 'THOUGHT', data.content);
    });

    socket.on('plan', (data) => {
        const planText = data.content.map((step, index) => `${index + 1}. ${step}`).join('\n');
        addAgentSection('plan', 'PLAN', planText);
    });

    socket.on('stream_start', (data) => {
        console.log('Stream starting:', data.type);
        if (data.type === 'assistant') {
            currentStreamingMessage = createStreamingMessage();
        }
    });

    socket.on('stream_chunk', (data) => {
        if (currentStreamingMessage && data.type === 'content') {
            appendToStreamingMessage(data.content);
        }
    });

    socket.on('stream_end', (data) => {
        console.log('Stream ended:', data.type);
        if (data.type === 'assistant') {
            finalizeStreamingMessage();
            currentStreamingMessage = null;
        }
    });

    socket.on('assistant_message', (data) => {
        addMessageToChat('assistant', data.content);
    });

    socket.on('tool_call_start', (data) => {
        addToolCall('start', data.name, data.arguments, data.id);
    });

    socket.on('tool_call_result', (data) => {
        addToolCall('result', data.name, data.result, data.id);
    });

    socket.on('tool_call_error', (data) => {
        addSystemMessage(`Tool error: ${data.message}`, 'error');
    });

    socket.on('final_answer', (data) => {
        addAgentSection('final-answer', 'FINAL ANSWER', data.content);
        isProcessing = false;
        updateSendButton();
    });

    socket.on('status', (data) => {
        const messageType = data.type || 'status';
        addSystemMessage(data.message, messageType);
    });

    socket.on('max_iterations', (data) => {
        addSystemMessage(data.message, 'warning');
        isProcessing = false;
        updateSendButton();
    });

    socket.on('message_complete', (data) => {
        console.log('Message processing complete:', data.response);
        isProcessing = false;
        updateSendButton();
    });

    socket.on('context_cleared', (data) => {
        addSystemMessage('Context cleared successfully');
    });

    socket.on('context_summary', (data) => {
        addSystemMessage(`Context: ${data.summary}`);
    });

    // Send message function
    const sendMessage = () => {
        const message = messageInput.value.trim();
        if (!message || isProcessing) return;

        // Add user message to chat
        addMessageToChat('user', message);
        messageInput.value = '';
        
        // Set processing state
        isProcessing = true;
        updateSendButton();

        // Send to server
        socket.emit('send_message', { message: message });
    };

    // Add message to chat
    const addMessageToChat = (sender, text) => {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', sender);
        
        const avatar = document.createElement('div');
        avatar.classList.add('avatar');
        avatar.textContent = sender === 'user' ? 'U' : 'A';
        
        const contentDiv = document.createElement('div');
        contentDiv.classList.add('message-content');
        
        const textDiv = document.createElement('div');
        textDiv.classList.add('message-text');
        textDiv.textContent = text;
        
        const timeDiv = document.createElement('div');
        timeDiv.classList.add('message-time');
        timeDiv.textContent = new Date().toLocaleTimeString();
        
        contentDiv.appendChild(textDiv);
        contentDiv.appendChild(timeDiv);
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(contentDiv);
        
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
        
        currentChat.push({ sender, text, timestamp: new Date() });
    };

    // Add system message
    const addSystemMessage = (text, type = 'info') => {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('system-message', type);
        messageDiv.textContent = text;
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    };

    // Add agent section (THOUGHT, PLAN, etc.)
    const addAgentSection = (className, label, content) => {
        const sectionDiv = document.createElement('div');
        sectionDiv.classList.add('agent-section', className);
        
        const labelDiv = document.createElement('div');
        labelDiv.classList.add('section-label');
        labelDiv.textContent = label;
        
        const contentDiv = document.createElement('div');
        contentDiv.classList.add('section-content');
        contentDiv.textContent = content;
        
        sectionDiv.appendChild(labelDiv);
        sectionDiv.appendChild(contentDiv);
        chatMessages.appendChild(sectionDiv);
        scrollToBottom();
    };

    // Add tool call info
    const addToolCall = (type, toolName, content, id) => {
        const existingCall = document.querySelector(`[data-tool-id="${id}"]`);
        
        if (type === 'start') {
            const toolDiv = document.createElement('div');
            toolDiv.classList.add('tool-call');
            toolDiv.setAttribute('data-tool-id', id);
            
            const headerDiv = document.createElement('div');
            headerDiv.classList.add('tool-header');
            headerDiv.innerHTML = `<strong>🔧 ${toolName}</strong> <small>(${id})</small>`;
            
            const argsDiv = document.createElement('div');
            argsDiv.classList.add('tool-arguments');
            argsDiv.textContent = `Arguments: ${content}`;
            
            const statusDiv = document.createElement('div');
            statusDiv.classList.add('tool-status');
            statusDiv.textContent = 'Executing...';
            
            toolDiv.appendChild(headerDiv);
            toolDiv.appendChild(argsDiv);
            toolDiv.appendChild(statusDiv);
            chatMessages.appendChild(toolDiv);
        } else if (type === 'result' && existingCall) {
            const statusDiv = existingCall.querySelector('.tool-status');
            if (statusDiv) {
                statusDiv.textContent = 'Completed';
                statusDiv.classList.add('completed');
            }
            
            const resultDiv = document.createElement('div');
            resultDiv.classList.add('tool-result');
            resultDiv.textContent = `Result: ${content}`;
            existingCall.appendChild(resultDiv);
        }
        
        scrollToBottom();
    };

    // Streaming message functions
    const createStreamingMessage = () => {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', 'assistant', 'streaming');
        
        const avatar = document.createElement('div');
        avatar.classList.add('avatar');
        avatar.textContent = 'A';
        
        const contentDiv = document.createElement('div');
        contentDiv.classList.add('message-content');
        
        const textDiv = document.createElement('div');
        textDiv.classList.add('message-text');
        textDiv.innerHTML = '<span class="cursor">▋</span>';
        
        const timeDiv = document.createElement('div');
        timeDiv.classList.add('message-time');
        timeDiv.textContent = new Date().toLocaleTimeString();
        
        contentDiv.appendChild(textDiv);
        contentDiv.appendChild(timeDiv);
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(contentDiv);
        
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
        
        return messageDiv;
    };

    const appendToStreamingMessage = (chunk) => {
        if (!currentStreamingMessage) return;
        
        const textDiv = currentStreamingMessage.querySelector('.message-text');
        const cursor = textDiv.querySelector('.cursor');
        
        // Insert chunk before cursor
        const textNode = document.createTextNode(chunk);
        textDiv.insertBefore(textNode, cursor);
        scrollToBottom();
    };

    const finalizeStreamingMessage = () => {
        if (!currentStreamingMessage) return;
        
        const cursor = currentStreamingMessage.querySelector('.cursor');
        if (cursor) {
            cursor.remove();
        }
        
        currentStreamingMessage.classList.remove('streaming');
    };

    // Utility functions
    const scrollToBottom = () => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    };

    const updateSendButton = () => {
        sendButton.disabled = isProcessing;
        sendButton.style.opacity = isProcessing ? '0.5' : '1';
        sendButton.innerHTML = isProcessing ? 
            '<div class="spinner"></div>' : 
            '<svg width="24" height="24" viewBox="0 0 24 24"><path d="M2 21L23 12L2 3V10L17 12L2 14V21Z"></path></svg>';
    };

    // File upload handling
    const handleFileUpload = () => {
        const input = document.createElement('input');
        input.type = 'file';
        input.onchange = (e) => {
            const file = e.target.files[0];
            if (file) {
                addMessageToChat('user', `📎 Uploaded file: ${file.name}`);
                // TODO: Implement file upload to server
            }
        };
        input.click();
    };

    // New chat function
    const startNewChat = () => {
        chatMessages.innerHTML = '<div class="logo-background"></div>';
        currentChat = [];
        socket.emit('clear_context');
    };

    // Create particles
    const createParticles = () => {
        const chatContainer = document.querySelector('.chat-container');
        const particlesContainer = document.createElement('div');
        particlesContainer.className = 'particles';
        
        for (let i = 0; i < 50; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            
            // Random properties
            const size = Math.random() * 4 + 1;
            const startPosition = Math.random() * 100;
            const delay = Math.random() * 5;
            
            particle.style.cssText = `
                width: ${size}px;
                height: ${size}px;
                left: ${Math.random() * 100}%;
                top: ${Math.random() * 100}%;
                animation-delay: -${delay}s;
                animation-duration: ${5 + Math.random() * 5}s;
            `;
            
            particlesContainer.appendChild(particle);
        }
        
        chatContainer.insertBefore(particlesContainer, chatContainer.firstChild);
    };

    createParticles();

    // Event listeners
    sendButton.addEventListener('click', sendMessage);
    fileButton.addEventListener('click', handleFileUpload);
    newChatButton.addEventListener('click', startNewChat);

    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Special commands
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Tab') {
            e.preventDefault();
            const value = messageInput.value;
            
            // Add some helpful shortcuts
            if (value === '/clear') {
                e.preventDefault();
                startNewChat();
                messageInput.value = '';
                return;
            }
            
            if (value === '/context') {
                e.preventDefault();
                socket.emit('get_context_summary');
                messageInput.value = '';
                return;
            }
        }
    });

    // Save API key to localStorage
    apiKeyInput.addEventListener('change', (e) => {
        localStorage.setItem('apiKey', e.target.value);
    });

    // Load saved API key
    const savedApiKey = localStorage.getItem('apiKey');
    if (savedApiKey) {
        apiKeyInput.value = savedApiKey;
    }

    // Initialize send button state
    updateSendButton();
});
