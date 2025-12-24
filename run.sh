#!/bin/bash
# Setup and run Vendora

echo "Setting up database..."
python3 setup_db.py

echo ""
echo "Starting Flask application..."
echo "Server will be available at http://localhost:5000"
echo "Default admin: admin@vendora.com / admin123"
echo ""
python3 app.py

