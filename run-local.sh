#!/bin/bash

# Script untuk menjalankan PDF Extractor Service di environment lokal

echo "🚀 Starting PDF Extractor Service (Local Development Mode)"
echo "========================================================="

# Check if virtual environment exists
if [[ ! -d "venv" ]]; then
    echo "❌ Virtual environment not found. Please run ./setup-dev.sh first"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env exists
if [[ ! -f ".env" ]]; then
    echo "⚙️  Creating .env from template..."
    cp .env.example .env
fi

# Check Redis connection
echo "🔍 Checking Redis connection..."
python3 -c "
import redis
try:
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.ping()
    print('✅ Redis connection successful')
except Exception as e:
    print('❌ Redis connection failed:', e)
    print('Please start Redis server:')
    print('  - Local: redis-server')
    print('  - Docker: docker run -d -p 6379:6379 redis:7-alpine')
    exit(1)
" || exit 1

# Create necessary directories
mkdir -p uploads temp logs

echo ""
echo "📋 Starting services..."
echo "======================="

# Function to handle cleanup
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $MASTER_PID 2>/dev/null
    kill $WORKER1_PID 2>/dev/null
    kill $WORKER2_PID 2>/dev/null
    echo "✅ Services stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start Master App
echo "🎯 Starting Master App..."
cd master_app
python main.py &
MASTER_PID=$!
cd ..

# Wait for master to start
echo "⏳ Waiting for Master App to start..."
sleep 3

# Check if master is running
if kill -0 $MASTER_PID 2>/dev/null; then
    echo "✅ Master App started (PID: $MASTER_PID)"
else
    echo "❌ Master App failed to start"
    exit 1
fi

# Start Worker Apps
echo "👷 Starting Worker 1..."
cd worker_app
python main.py &
WORKER1_PID=$!
cd ..

echo "👷 Starting Worker 2..."
cd worker_app
python main.py &
WORKER2_PID=$!
cd ..

sleep 2

# Check workers
RUNNING_WORKERS=0
if kill -0 $WORKER1_PID 2>/dev/null; then
    echo "✅ Worker 1 started (PID: $WORKER1_PID)"
    ((RUNNING_WORKERS++))
fi

if kill -0 $WORKER2_PID 2>/dev/null; then
    echo "✅ Worker 2 started (PID: $WORKER2_PID)"
    ((RUNNING_WORKERS++))
fi

echo ""
echo "📊 Service Status:"
echo "=================="
echo "🎯 Master App: http://localhost:8000"
echo "👷 Workers: $RUNNING_WORKERS running"
echo "📖 API Docs: http://localhost:8000/docs"
echo "🔍 Health: http://localhost:8000/health"
echo ""
echo "� Project Directories:"
echo "  📂 Uploads: $(pwd)/uploads/"
echo "  📂 Temp: $(pwd)/temp/"
echo "  📂 Logs: $(pwd)/logs/"
echo ""
echo "�📝 Logs are saved to logs/ directory"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for processes
wait