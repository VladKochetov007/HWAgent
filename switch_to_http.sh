#!/bin/bash

# Switch to HTTP mode for frontend compatibility
# Usage: ./switch_to_http.sh

set -e

echo "🔄 Switching to HTTP mode for frontend compatibility..."

# Configuration
PROJECT_PATH="/root/HWAgent"
SERVICE_NAME="hwagent-api"

echo "🛑 Stopping services..."
sudo systemctl stop nginx

echo "🔧 Switching to hybrid HTTP/HTTPS configuration..."
sudo cp ${PROJECT_PATH}/nginx-hybrid.conf /etc/nginx/sites-available/hwagent

echo "🔄 Testing nginx configuration..."
sudo nginx -t

echo "🚀 Starting nginx..."
sudo systemctl start nginx

echo "🌐 Updating firewall to allow HTTP..."
sudo ufw allow 80/tcp

echo "📊 Checking service status..."
sudo systemctl status nginx --no-pager
sudo systemctl status ${SERVICE_NAME} --no-pager

echo "✅ HTTP mode activated!"
echo ""
echo "🔗 Your API is now available at:"
echo "  • HTTP:  http://91.108.121.43"
echo "  • HTTPS: https://91.108.121.43 (self-signed)"
echo "  • API docs: http://91.108.121.43/docs"
echo "  • Health: http://91.108.121.43/health"
echo ""
echo "📱 For your frontend, use:"
echo "  • Local dev: http://91.108.121.43"
echo "  • GitHub Pages: https://91.108.121.43 (after accepting cert)"
echo ""
echo "🧪 Test CORS:"
echo "curl -H 'Origin: https://your-username.github.io' http://91.108.121.43/health" 