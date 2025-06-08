#!/bin/bash

# Let's Encrypt SSL Setup for HWAgent
# Usage: ./setup_letsencrypt.sh your@email.com

set -e

if [ -z "$1" ]; then
    echo "❌ Usage: ./setup_letsencrypt.sh your@email.com"
    exit 1
fi

EMAIL="$1"
DOMAIN="91.108.121.43"

echo "🔐 Setting up Let's Encrypt SSL for HWAgent API..."

echo "📦 Installing certbot..."
sudo apt update
sudo apt install -y certbot python3-certbot-nginx

echo "🛑 Stopping nginx temporarily..."
sudo systemctl stop nginx

echo "🔑 Obtaining SSL certificate from Let's Encrypt..."
sudo certbot certonly --standalone \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    --domains "$DOMAIN"

echo "🔧 Updating nginx configuration for Let's Encrypt..."
# Update nginx config to use Let's Encrypt certificates
sudo sed -i "s|ssl_certificate /etc/ssl/certs/hwagent.crt;|ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;|g" /etc/nginx/sites-available/hwagent
sudo sed -i "s|ssl_certificate_key /etc/ssl/private/hwagent.key;|ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;|g" /etc/nginx/sites-available/hwagent

echo "🔄 Testing nginx configuration..."
sudo nginx -t

echo "🚀 Starting nginx..."
sudo systemctl start nginx

echo "🔄 Setting up automatic renewal..."
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer

# Test renewal
sudo certbot renew --dry-run

echo "✅ Let's Encrypt SSL setup completed!"
echo ""
echo "🔗 Your API is now available with trusted SSL at:"
echo "  • HTTPS: https://$DOMAIN"
echo "  • API docs: https://$DOMAIN/docs"
echo "  • Health check: https://$DOMAIN/health"
echo ""
echo "✅ Certificate will auto-renew every 60 days"
echo ""
echo "📋 Certificate info:"
sudo certbot certificates 