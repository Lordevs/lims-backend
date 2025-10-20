#!/bin/bash

# LIMS Backend Deployment Script
# This script sets up Django with Gunicorn and Nginx

set -e  # Exit on error

PROJECT_DIR="/var/www/myproject/lims-backend"
VENV_DIR="$PROJECT_DIR/venv"

echo "========================================="
echo "LIMS Backend Deployment Script"
echo "========================================="
echo ""

# Create necessary directories
echo "Creating necessary directories..."
sudo mkdir -p /var/log/gunicorn
sudo mkdir -p /var/run/gunicorn
sudo mkdir -p /var/log/nginx
sudo mkdir -p $PROJECT_DIR/staticfiles
sudo mkdir -p $PROJECT_DIR/media

# Set proper permissions
echo "Setting permissions..."
sudo chown -R www-data:www-data /var/log/gunicorn
sudo chown -R www-data:www-data /var/run/gunicorn
sudo chown -R www-data:www-data $PROJECT_DIR/staticfiles
sudo chown -R www-data:www-data $PROJECT_DIR/media

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv $VENV_DIR
fi

# Activate virtual environment
echo "Activating virtual environment..."
source $VENV_DIR/bin/activate

# Install/upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing Python dependencies..."
pip install -r $PROJECT_DIR/requirements.txt

# Collect static files
echo "Collecting static files..."
cd $PROJECT_DIR
python manage.py collectstatic --noinput

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Copy systemd service file
echo "Setting up systemd service..."
sudo cp $PROJECT_DIR/lims-gunicorn.service /etc/systemd/system/

# Copy nginx configuration
echo "Setting up Nginx configuration..."
sudo cp $PROJECT_DIR/lims-nginx.conf /etc/nginx/sites-available/lims-backend
sudo ln -sf /etc/nginx/sites-available/lims-backend /etc/nginx/sites-enabled/

# Remove default nginx site if it exists
if [ -f /etc/nginx/sites-enabled/default ]; then
    echo "Removing default Nginx site..."
    sudo rm /etc/nginx/sites-enabled/default
fi

# Test nginx configuration
echo "Testing Nginx configuration..."
sudo nginx -t

# Reload systemd
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

# Enable and start Gunicorn service
echo "Enabling and starting Gunicorn service..."
sudo systemctl enable lims-gunicorn
sudo systemctl restart lims-gunicorn

# Restart Nginx
echo "Restarting Nginx..."
sudo systemctl restart nginx

# Check service status
echo ""
echo "========================================="
echo "Deployment Complete!"
echo "========================================="
echo ""
echo "Service Status:"
echo "---------------"
sudo systemctl status lims-gunicorn --no-pager
echo ""
echo "Nginx Status:"
echo "-------------"
sudo systemctl status nginx --no-pager
echo ""
echo "Your application should now be accessible at http://your-server-ip/"
echo ""
echo "Useful commands:"
echo "  - View Gunicorn logs: sudo journalctl -u lims-gunicorn -f"
echo "  - View Nginx access logs: sudo tail -f /var/log/nginx/lims_access.log"
echo "  - View Nginx error logs: sudo tail -f /var/log/nginx/lims_error.log"
echo "  - Restart Gunicorn: sudo systemctl restart lims-gunicorn"
echo "  - Restart Nginx: sudo systemctl restart nginx"

