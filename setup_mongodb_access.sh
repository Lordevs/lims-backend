#!/bin/bash

# MongoDB Remote Access Setup Script
# Choose your preferred method

echo "=========================================="
echo "MongoDB Remote Access Setup"
echo "=========================================="
echo ""
echo "Choose your connection method:"
echo ""
echo "1) SSH Tunnel (RECOMMENDED - Most Secure)"
echo "   - No MongoDB config changes needed"
echo "   - Encrypted connection"
echo "   - MongoDB stays on localhost"
echo ""
echo "2) Direct Connection with Authentication"
echo "   - Exposes MongoDB to internet"
echo "   - Requires authentication setup"
echo "   - Less secure but no SSH needed"
echo ""
echo "3) Show connection information only"
echo ""
read -p "Enter your choice (1-3): " choice

case $choice in
  1)
    echo ""
    echo "=========================================="
    echo "SSH Tunnel Setup (Recommended)"
    echo "=========================================="
    echo ""
    echo "No server-side changes needed!"
    echo ""
    echo "On YOUR LOCAL MACHINE, run this command:"
    echo ""
    echo "  ssh -L 27017:localhost:27017 root@72.60.196.229"
    echo ""
    echo "Keep that terminal open, then connect using:"
    echo ""
    echo "MongoDB Compass:"
    echo "  mongodb://localhost:27017/lims"
    echo ""
    echo "MongoDB Shell:"
    echo "  mongosh mongodb://localhost:27017/lims"
    echo ""
    echo "Python:"
    echo "  from pymongo import MongoClient"
    echo "  client = MongoClient('mongodb://localhost:27017/')"
    echo "  db = client['lims']"
    echo ""
    ;;
    
  2)
    echo ""
    echo "=========================================="
    echo "Direct Connection Setup"
    echo "=========================================="
    echo ""
    echo "WARNING: This will expose MongoDB to the internet!"
    echo ""
    read -p "Are you sure? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
      echo "Aborted."
      exit 0
    fi
    
    echo ""
    echo "Step 1: Creating MongoDB admin user..."
    read -p "Enter admin password (or press Enter for auto-generated): " admin_pass
    
    if [ -z "$admin_pass" ]; then
      admin_pass=$(openssl rand -base64 24)
      echo "Generated admin password: $admin_pass"
    fi
    
    read -p "Enter lims_user password (or press Enter for auto-generated): " lims_pass
    
    if [ -z "$lims_pass" ]; then
      lims_pass=$(openssl rand -base64 24)
      echo "Generated lims_user password: $lims_pass"
    fi
    
    echo ""
    echo "Creating users..."
    
    mongosh --eval "
    use admin
    db.createUser({
      user: 'admin',
      pwd: '$admin_pass',
      roles: [{ role: 'root', db: 'admin' }]
    })
    
    use lims
    db.createUser({
      user: 'lims_user',
      pwd: '$lims_pass',
      roles: [{ role: 'readWrite', db: 'lims' }]
    })
    " 2>/dev/null
    
    echo ""
    echo "Step 2: Updating MongoDB configuration..."
    
    sudo cp /etc/mongod.conf /etc/mongod.conf.backup
    
    sudo sed -i 's/bindIp: 127.0.0.1/bindIp: 0.0.0.0/' /etc/mongod.conf
    
    if ! grep -q "^security:" /etc/mongod.conf; then
      echo "" | sudo tee -a /etc/mongod.conf
      echo "security:" | sudo tee -a /etc/mongod.conf
      echo "  authorization: enabled" | sudo tee -a /etc/mongod.conf
    fi
    
    echo ""
    echo "Step 3: Configuring firewall..."
    sudo ufw allow 27017/tcp
    
    echo ""
    echo "Step 4: Restarting MongoDB..."
    sudo systemctl restart mongod
    
    sleep 3
    
    if sudo systemctl is-active --quiet mongod; then
      echo "✅ MongoDB restarted successfully"
    else
      echo "❌ MongoDB failed to restart. Restoring backup..."
      sudo cp /etc/mongod.conf.backup /etc/mongod.conf
      sudo systemctl restart mongod
      exit 1
    fi
    
    echo ""
    echo "Step 5: Updating Django .env file..."
    cd /var/www/myproject/lims-backend
    
    sed -i "s|MONGODB_USERNAME=|MONGODB_USERNAME=lims_user|" .env
    sed -i "s|MONGODB_PASSWORD=|MONGODB_PASSWORD=$lims_pass|" .env
    
    sudo systemctl restart lims-gunicorn
    
    echo ""
    echo "=========================================="
    echo "✅ Setup Complete!"
    echo "=========================================="
    echo ""
    echo "Connection Details:"
    echo "-------------------"
    echo "Server: 72.60.196.229"
    echo "Port: 27017"
    echo "Database: lims"
    echo "Username: lims_user"
    echo "Password: $lims_pass"
    echo ""
    echo "Connection String:"
    echo "mongodb://lims_user:$lims_pass@72.60.196.229:27017/lims"
    echo ""
    echo "MongoDB Compass:"
    echo "mongodb://lims_user:$lims_pass@72.60.196.229:27017/lims"
    echo ""
    echo "⚠️  SAVE THESE CREDENTIALS SECURELY!"
    echo ""
    echo "Admin credentials (for MongoDB management):"
    echo "Username: admin"
    echo "Password: $admin_pass"
    echo ""
    
    # Save credentials to file
    cat > /root/mongodb_credentials.txt << EOF
MongoDB Credentials
===================
Created: $(date)

Admin User:
  Username: admin
  Password: $admin_pass
  Connection: mongodb://admin:$admin_pass@72.60.196.229:27017/admin

Application User:
  Username: lims_user
  Password: $lims_pass
  Connection: mongodb://lims_user:$lims_pass@72.60.196.229:27017/lims

⚠️  Keep this file secure and delete after saving credentials elsewhere!
EOF
    
    echo "Credentials saved to: /root/mongodb_credentials.txt"
    echo ""
    ;;
    
  3)
    echo ""
    echo "=========================================="
    echo "Current MongoDB Information"
    echo "=========================================="
    echo ""
    echo "Server IP: 72.60.196.229"
    echo "MongoDB Port: 27017"
    echo "Database Name: lims"
    echo ""
    echo "Current Configuration:"
    grep -A 2 "^net:" /etc/mongod.conf
    echo ""
    echo "MongoDB Status:"
    sudo systemctl status mongod --no-pager | head -5
    echo ""
    echo "For connection methods, see:"
    echo "  /var/www/myproject/lims-backend/MONGODB_REMOTE_ACCESS.md"
    echo ""
    ;;
    
  *)
    echo "Invalid choice. Exiting."
    exit 1
    ;;
esac

echo ""
echo "For detailed documentation, see:"
echo "  /var/www/myproject/lims-backend/MONGODB_REMOTE_ACCESS.md"
echo ""


