#!/bin/bash
# Setup and run Vendora

echo "Setting up database..."
python3 setup_db.py

echo ""
echo "Starting Flask application..."
echo "Server will be available at http://localhost:5000"
echo "Admin: set VENDORA_BOOTSTRAP_ADMIN_EMAIL and VENDORA_BOOTSTRAP_ADMIN_PASSWORD to create/reset an admin"
echo ""
python3 app.py

