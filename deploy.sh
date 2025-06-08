#!/bin/bash

# HWAgent Backend Deployment Script
# Usage: ./deploy.sh

set -e

echo "🚀 Deploying HWAgent Backend to VPS..."

# Configuration
VPS_IP="91.108.121.43"
PROJECT_PATH="/root/HWagent"
SERVICE_NAME="hwagent-api"

echo "📦 Installing/updating dependencies..."
# Activate virtual environment and install dependencies
source ${PROJECT_PATH}/.venv/bin/activate
pip install -r ${PROJECT_PATH}/requirements.txt

echo "🔧 Setting up systemd service..."
# Update service file with correct paths
sed -i "s|/root/HWagent|${PROJECT_PATH}|g" ${PROJECT_PATH}/hwagent-api.service

# Copy service file to systemd directory
sudo cp ${PROJECT_PATH}/hwagent-api.service /etc/systemd/system/

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}

echo "🔥 Starting the service..."
sudo systemctl restart ${SERVICE_NAME}

echo "📊 Checking service status..."
sudo systemctl status ${SERVICE_NAME}

echo "🌐 Setting up firewall (if needed)..."
# Open port 8000 if firewall is active
if command -v ufw &> /dev/null; then
    sudo ufw allow 8000/tcp
    echo "✅ Port 8000 opened in UFW firewall"
fi

echo "✅ Deployment completed!"
echo "🔗 Your API is available at: http://${VPS_IP}:8000"
echo "📖 API docs: http://${VPS_IP}:8000/docs"
echo "🏥 Health check: http://${VPS_IP}:8000/health"

echo ""
echo "📋 Useful commands:"
echo "  • Check status: sudo systemctl status ${SERVICE_NAME}"
echo "  • View logs: sudo journalctl -u ${SERVICE_NAME} -f"
echo "  • Restart: sudo systemctl restart ${SERVICE_NAME}"
echo "  • Stop: sudo systemctl stop ${SERVICE_NAME}" 