// Configuration for HWAgent Frontend
const CONFIG = {
    // Development configuration
    development: {
        API_BASE: 'http://localhost:8000',
        APP_NAME: 'HWAgent Dev',
        DEBUG: true
    },
    
    // Production configuration (GitHub Pages + VPS API)
    production: {
        API_BASE: 'https://your-domain.com',  // Replace with your VPS domain
        APP_NAME: 'HWAgent',
        DEBUG: false
    }
};

// Auto-detect environment
const ENVIRONMENT = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
    ? 'development' 
    : 'production';

// Export current configuration
const CURRENT_CONFIG = CONFIG[ENVIRONMENT];

console.log(`🚀 HWAgent running in ${ENVIRONMENT} mode`);
console.log(`📡 API Base: ${CURRENT_CONFIG.API_BASE}`); 