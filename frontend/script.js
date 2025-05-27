document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const messageInput = document.getElementById('message-input');
    const sendButton = document.querySelector('.send-message');
    const fileButton = document.querySelector('.upload-file');
    const chatMessages = document.getElementById('chat-messages');
    const newChatButton = document.getElementById('new-chat');
    const modelSelect = document.getElementById('model-select');
    const apiKeyInput = document.querySelector('.api-input input');
    const themeToggle = document.getElementById('theme-toggle');

    // Chat history management
    const historyList = document.getElementById('history-list');
    let currentChat = [];

    // Send message function
    const sendMessage = () => {
        const message = messageInput.value.trim();
        if (!message) return;

        // Add user message to chat
        addMessageToChat('user', message);
        messageInput.value = '';

        // Simulate AI response (replace with actual API call)
        setTimeout(() => {
            addMessageToChat('ai', `Response to: ${message}`);
        }, 1000);
    };

    // Add message to chat
    const addMessageToChat = (sender, text) => {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', sender);
        messageDiv.innerHTML = `
            <div class="message-content">
                <div class="message-text">${text}</div>
                <div class="message-time">${new Date().toLocaleTimeString()}</div>
            </div>
        `;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        currentChat.push({ sender, text });
    };

    // File upload handling
    const handleFileUpload = () => {
        const input = document.createElement('input');
        input.type = 'file';
        input.onchange = (e) => {
            const file = e.target.files[0];
            if (file) {
                addMessageToChat('user', `Uploaded file: ${file.name}`);
            }
        };
        input.click();
    };

    // New chat function
    const startNewChat = () => {
        chatMessages.innerHTML = '<div class="logo-background"></div>';
        currentChat = [];
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

    // Save API key to localStorage
    apiKeyInput.addEventListener('change', (e) => {
        localStorage.setItem('apiKey', e.target.value);
    });

    // Load saved API key
    const savedApiKey = localStorage.getItem('apiKey');
    if (savedApiKey) {
        apiKeyInput.value = savedApiKey;
    }
});
