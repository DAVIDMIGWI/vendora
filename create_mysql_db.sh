#!/bin/bash
# Script to create MySQL database for Smart Soko

echo "🔧 Setting up MySQL database for Smart Soko..."
echo ""

# Check if MySQL is running
if ! mysql -u root -e "SELECT 1" &>/dev/null; then
    echo "❌ MySQL server is not running!"
    echo ""
    echo "Please start MySQL first:"
    echo "  • macOS (Homebrew): brew services start mysql"
    echo "  • macOS (MySQL): sudo /usr/local/mysql/support-files/mysql.server start"
    echo "  • Linux: sudo systemctl start mysql"
    echo ""
    exit 1
fi

echo "✓ MySQL server is running"
echo ""

# Get MySQL credentials
read -p "MySQL username [root]: " MYSQL_USER
MYSQL_USER=${MYSQL_USER:-root}

read -sp "MySQL password: " MYSQL_PASS
echo ""

# Create databases
echo ""
echo "Creating databases..."

mysql -u "$MYSQL_USER" -p"$MYSQL_PASS" <<EOF
CREATE DATABASE IF NOT EXISTS smart_soko_dev CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS smart_soko CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EOF

if [ $? -eq 0 ]; then
    echo "✓ Database 'smart_soko_dev' created"
    echo "✓ Database 'smart_soko' created"
    echo ""
    echo "✅ MySQL database setup complete!"
    echo ""
    echo "Update config.py with your MySQL credentials if different from:"
    echo "  Username: root"
    echo "  Password: (your password)"
else
    echo "❌ Failed to create database. Please check your MySQL credentials."
    exit 1
fi

