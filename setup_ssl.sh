#!/bin/bash

# SSL Setup Script for HWAgent
# Usage: ./setup_ssl.sh

set -e

echo "🔐 Setting up SSL for HWAgent API..."

# Configuration
PROJECT_PATH="/root/HWAgent"
SERVICE_NAME="hwagent-api"
DOMAIN="91.108.121.43"

echo "📦 Installing nginx..."
sudo apt update
sudo apt install -y nginx

echo "🛑 Stopping nginx for setup..."
sudo systemctl stop nginx

echo "🔑 Generating self-signed SSL certificate..."
sudo mkdir -p /etc/ssl/certs /etc/ssl/private

# Generate private key
sudo openssl genrsa -out /etc/ssl/private/hwagent.key 2048

# Generate certificate signing request
sudo openssl req -new -key /etc/ssl/private/hwagent.key -out /etc/ssl/certs/hwagent.csr -subj "/C=US/ST=State/L=City/O=Organization/CN=${DOMAIN}"

# Generate self-signed certificate valid for 1 year
sudo openssl x509 -req -days 365 -in /etc/ssl/certs/hwagent.csr -signkey /etc/ssl/private/hwagent.key -out /etc/ssl/certs/hwagent.crt

# Set proper permissions
sudo chmod 600 /etc/ssl/private/hwagent.key
sudo chmod 644 /etc/ssl/certs/hwagent.crt

echo "🔧 Configuring nginx..."
# Remove default nginx config
sudo rm -f /etc/nginx/sites-enabled/default

# Copy our nginx config
sudo cp ${PROJECT_PATH}/nginx-hwagent.conf /etc/nginx/sites-available/hwagent
sudo ln -sf /etc/nginx/sites-available/hwagent /etc/nginx/sites-enabled/

# Test nginx configuration
sudo nginx -t

echo "🔄 Updating HWAgent service..."
sudo systemctl stop ${SERVICE_NAME}
sudo cp ${PROJECT_PATH}/hwagent-api.service /etc/systemd/system/
sudo systemctl daemon-reload

echo "🚀 Starting services..."
sudo systemctl start ${SERVICE_NAME}
sudo systemctl start nginx
sudo systemctl enable nginx

echo "🌐 Configuring firewall..."
# Open HTTPS port and close direct API port
sudo ufw allow 443/tcp
sudo ufw allow 80/tcp
sudo ufw delete allow 8000/tcp 2>/dev/null || true

echo "📊 Checking service status..."
sudo systemctl status ${SERVICE_NAME} --no-pager
sudo systemctl status nginx --no-pager

echo "✅ SSL setup completed!"
echo ""
echo "🔗 Your API is now available at:"
echo "  • HTTPS: https://${DOMAIN}"
echo "  • API docs: https://${DOMAIN}/docs"
echo "  • Health check: https://${DOMAIN}/health"
echo ""
echo "⚠️  NOTE: Using self-signed certificate!"
echo "   Browsers will show security warning - click 'Advanced' → 'Proceed'"
echo ""
echo "🔍 For production, consider using Let's Encrypt:"
echo "   sudo apt install certbot python3-certbot-nginx"
echo "   sudo certbot --nginx -d ${DOMAIN}"
echo ""
echo "📋 Useful commands:"
echo "  • Check nginx: sudo systemctl status nginx"
echo "  • Check API: sudo systemctl status ${SERVICE_NAME}"
echo "  • View nginx logs: sudo tail -f /var/log/nginx/error.log"
echo "  • Restart all: sudo systemctl restart ${SERVICE_NAME} nginx" 