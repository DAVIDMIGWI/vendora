#!/bin/bash
# Start Smart Soko server with debug mode

cd "$(dirname "$0")"

echo "🚀 Starting Smart Soko server..."
echo ""

# Check if server is already running
if lsof -ti:5001 > /dev/null 2>&1; then
    echo "⚠️  Server is already running on port 5001"
    echo "   Stopping existing server..."
    lsof -ti:5001 | xargs kill -9 2>/dev/null
    sleep 2
fi

# Start server in background
nohup python3 app.py > app.log 2>&1 &
SERVER_PID=$!

sleep 3

# Check if server started successfully
if ps -p $SERVER_PID > /dev/null; then
    echo "✅ Server started successfully!"
    echo "   PID: $SERVER_PID"
    echo "   URL: http://localhost:5001"
    echo "   Logs: app.log"
    echo ""
    echo "To stop the server:"
    echo "   kill $SERVER_PID"
    echo "   or: ./stop_server.sh"
    echo ""
    echo "To view logs:"
    echo "   tail -f app.log"
else
    echo "❌ Failed to start server. Check app.log for errors."
    exit 1
fi

