#!/bin/bash

# SSL Certificate Setup Script for api.gripcolims.com
# Run this AFTER your DNS is properly configured and propagated

set -e

DOMAIN="api.gripcolims.com"
EMAIL="your-email@example.com"  # Change this to your email

echo "========================================="
echo "SSL Certificate Setup"
echo "========================================="
echo ""
echo "Domain: $DOMAIN"
echo ""

# Check if domain resolves
echo "Checking DNS resolution..."
if ! nslookup $DOMAIN > /dev/null 2>&1; then
    echo "ERROR: Domain $DOMAIN does not resolve yet!"
    echo "Please wait for DNS propagation and try again."
    echo "You can check DNS status at: https://dnschecker.org/#A/$DOMAIN"
    exit 1
fi

RESOLVED_IP=$(nslookup $DOMAIN | grep -A1 "Name:" | grep "Address:" | awk '{print $2}')
SERVER_IP=$(hostname -I | awk '{print $1}')

echo "Domain resolves to: $RESOLVED_IP"
echo "Server IP is: $SERVER_IP"

if [ "$RESOLVED_IP" != "$SERVER_IP" ]; then
    echo "WARNING: Domain resolves to $RESOLVED_IP but server IP is $SERVER_IP"
    echo "Please verify your DNS configuration."
    read -p "Do you want to continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Install Certbot if not already installed
if ! command -v certbot &> /dev/null; then
    echo "Installing Certbot..."
    sudo apt update
    sudo apt install certbot python3-certbot-nginx -y
else
    echo "Certbot is already installed."
fi

# Obtain SSL certificate
echo ""
echo "Obtaining SSL certificate for $DOMAIN..."
echo "You will be prompted to:"
echo "  1. Enter your email address"
echo "  2. Agree to Terms of Service"
echo "  3. Choose whether to redirect HTTP to HTTPS (recommended: Yes)"
echo ""

sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email $EMAIL --redirect || {
    echo "ERROR: Failed to obtain SSL certificate"
    echo "Please make sure:"
    echo "  1. Port 80 is open (sudo ufw allow 80/tcp)"
    echo "  2. Port 443 is open (sudo ufw allow 443/tcp)"
    echo "  3. Nginx is running (sudo systemctl status nginx)"
    echo "  4. Domain resolves correctly"
    exit 1
}

# Update Django .env for HTTPS
echo ""
echo "Updating Django configuration for HTTPS..."
cd /var/www/myproject/lims-backend

# Backup .env
cp .env .env.before-ssl

# Update CSRF_TRUSTED_ORIGINS to prioritize HTTPS
cat > .env << 'EOF'
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017/lims
MONGODB_NAME=lims
MONGODB_USERNAME=
MONGODB_PASSWORD=
MONGODB_AUTH_SOURCE=admin

# Django Configuration
SECRET_KEY=django-insecure-igwv3+0(xwh@s7wvvviq6(40#vy#x44x$)u1p4=d$03#94!4)7
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,72.60.196.229,api.gripcolims.com
CSRF_TRUSTED_ORIGINS=https://api.gripcolims.com,http://api.gripcolims.com

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production
EOF

# Restart Gunicorn
echo "Restarting Gunicorn..."
sudo systemctl restart lims-gunicorn

# Test certificate
echo ""
echo "Testing certificate auto-renewal..."
sudo certbot renew --dry-run

echo ""
echo "========================================="
echo "SSL Setup Complete!"
echo "========================================="
echo ""
echo "Your site is now accessible via HTTPS:"
echo "  https://$DOMAIN/"
echo "  https://$DOMAIN/health/"
echo "  https://$DOMAIN/admin/"
echo "  https://$DOMAIN/api/"
echo ""
echo "HTTP requests will automatically redirect to HTTPS"
echo ""
echo "Certificate will auto-renew before expiration."
echo ""
echo "Useful commands:"
echo "  - Check certificate: sudo certbot certificates"
echo "  - Renew certificate: sudo certbot renew"
echo "  - View Nginx SSL config: sudo cat /etc/nginx/sites-available/lims-backend"
echo ""

