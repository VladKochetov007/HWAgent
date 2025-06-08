#!/bin/bash

# Update HWAgent Service Script
# Usage: ./update_service.sh

set -e

echo "🔄 Updating HWAgent service configuration..."

# Configuration
PROJECT_PATH="/root/HWAgent"
SERVICE_NAME="hwagent-api"

echo "🛑 Stopping current service..."
sudo systemctl stop ${SERVICE_NAME}

echo "🔧 Updating service file with correct PATH..."
# Copy updated service file to systemd directory
sudo cp ${PROJECT_PATH}/hwagent-api.service /etc/systemd/system/

echo "🔄 Reloading systemd daemon..."
sudo systemctl daemon-reload

echo "🚀 Starting service..."
sudo systemctl start ${SERVICE_NAME}

echo "📊 Checking service status..."
sudo systemctl status ${SERVICE_NAME}

echo "✅ Service update completed!"
echo "🔗 Your API should be available at: http://91.108.121.43:8000"
echo "🧪 Test LaTeX: The service should now have access to pdflatex"

echo ""
echo "📋 Useful commands:"
echo "  • Check status: sudo systemctl status ${SERVICE_NAME}"
echo "  • View logs: sudo journalctl -u ${SERVICE_NAME} -f"
echo "  • Test pdflatex: sudo systemctl show hwagent-api --property=Environment" 