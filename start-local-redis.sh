#!/bin/bash

# Quick start script for local testing with Redis

echo "🚀 Starting YouTube Downloader with Redis..."
echo ""

# Check if Redis is running
echo "📡 Checking Redis..."
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis is not running!"
    echo ""
    echo "Please start Redis first:"
    echo "  - Windows WSL: sudo service redis-server start"
    echo "  - Mac: brew services start redis"
    echo "  - Linux: sudo systemctl start redis-server"
    echo ""
    exit 1
fi

echo "✅ Redis is running"
echo ""

# Start backend
echo "🐍 Starting Backend..."
cd backend
export REDIS_HOST=localhost
export REDIS_PORT=6379
export MAX_PARALLEL_DOWNLOADS=3
export CORS_ORIGINS="http://localhost:3000"

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1

# Start backend in background
python main.py &
BACKEND_PID=$!
echo "✅ Backend started (PID: $BACKEND_PID)"
echo ""

# Wait for backend to start
sleep 3

# Start frontend
echo "⚛️  Starting Frontend..."
cd ../frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing npm packages..."
    npm install > /dev/null 2>&1
fi

# Create env file
echo "REACT_APP_API_URL=http://localhost:8000" > .env.development

# Start frontend
npm start &
FRONTEND_PID=$!
echo "✅ Frontend started (PID: $FRONTEND_PID)"
echo ""

echo "🎉 Application is running!"
echo ""
echo "📍 URLs:"
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:3000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "⚙️  Configuration:"
echo "   Redis: localhost:6379"
echo "   Max Parallel Downloads: 3"
echo ""
echo "📝 To stop the application:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "💡 Test batch downloads:"
echo "   1. Go to http://localhost:3000"
echo "   2. Click 'Batch Download' tab"
echo "   3. Add multiple YouTube URLs"
echo "   4. Click 'Download All'"
echo ""

# Wait for user interrupt
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo ''; echo '👋 Stopped'; exit" INT
wait
