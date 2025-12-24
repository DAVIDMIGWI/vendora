#!/bin/bash
# Stop Smart Soko server

echo "🛑 Stopping Smart Soko server..."

# Find and kill server process
if lsof -ti:5001 > /dev/null 2>&1; then
    lsof -ti:5001 | xargs kill -9 2>/dev/null
    echo "✅ Server stopped"
else
    echo "ℹ️  No server running on port 5001"
fi

# Also kill any python3 app.py processes
pkill -f "python3 app.py" 2>/dev/null

