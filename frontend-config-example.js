// Frontend API Configuration
// Add this to your frontend project

// Auto-detect environment and set appropriate API URL
const getApiUrl = () => {
    const hostname = window.location.hostname;
    const protocol = window.location.protocol;
    
    // Local development
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
        return 'http://91.108.121.43';
    }
    
    // GitHub Pages (HTTPS)
    if (hostname.includes('github.io')) {
        // Try HTTPS first, fallback to HTTP if needed
        return 'https://91.108.121.43';
    }
    
    // Default fallback
    return 'http://91.108.121.43';
};

// API Configuration
const API_CONFIG = {
    BASE_URL: getApiUrl(),
    TIMEOUT: 30000,
    HEADERS: {
        'Content-Type': 'application/json',
    }
};

// Example API call with error handling
const callAPI = async (endpoint, options = {}) => {
    const url = `${API_CONFIG.BASE_URL}${endpoint}`;
    
    try {
        const response = await fetch(url, {
            timeout: API_CONFIG.TIMEOUT,
            headers: API_CONFIG.HEADERS,
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        
        // If HTTPS fails and we're on GitHub Pages, try HTTP
        if (url.startsWith('https://') && window.location.hostname.includes('github.io')) {
            console.log('HTTPS failed, trying HTTP...');
            const httpUrl = url.replace('https://', 'http://');
            
            try {
                const httpResponse = await fetch(httpUrl, {
                    timeout: API_CONFIG.TIMEOUT,
                    headers: API_CONFIG.HEADERS,
                    ...options
                });
                
                if (httpResponse.ok) {
                    return await httpResponse.json();
                }
            } catch (httpError) {
                console.error('HTTP fallback also failed:', httpError);
            }
        }
        
        throw error;
    }
};

// Usage examples:
// const health = await callAPI('/health');
// const taskResult = await callAPI('/run-task', {
//     method: 'POST',
//     body: JSON.stringify({ task: 'Hello world' })
// });

console.log('API configured for:', API_CONFIG.BASE_URL); 