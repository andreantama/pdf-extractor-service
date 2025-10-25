#!/bin/bash

# Script untuk menghentikan semua process PDF Extractor Service

echo "🛑 Stopping PDF Extractor Service (Local Development)"
echo "==================================================="

# Find dan kill process berdasarkan nama
echo "🔍 Looking for running processes..."

# Kill master app processes
MASTER_PIDS=$(pgrep -f "master_app/main.py")
if [[ -n "$MASTER_PIDS" ]]; then
    echo "🎯 Stopping Master App processes: $MASTER_PIDS"
    kill $MASTER_PIDS
    sleep 1
    # Force kill if still running
    kill -9 $MASTER_PIDS 2>/dev/null
else
    echo "📝 No Master App processes found"
fi

# Kill worker app processes  
WORKER_PIDS=$(pgrep -f "worker_app/main.py")
if [[ -n "$WORKER_PIDS" ]]; then
    echo "👷 Stopping Worker App processes: $WORKER_PIDS"
    kill $WORKER_PIDS
    sleep 1
    # Force kill if still running
    kill -9 $WORKER_PIDS 2>/dev/null
else
    echo "📝 No Worker App processes found"
fi

# Kill any python processes yang mungkin terkait
PDF_PIDS=$(pgrep -f "pdf.*extractor")
if [[ -n "$PDF_PIDS" ]]; then
    echo "🔧 Stopping other PDF extractor processes: $PDF_PIDS"
    kill $PDF_PIDS 2>/dev/null
fi

# Check untuk uvicorn processes pada port 8000
UVICORN_PIDS=$(lsof -t -i:8000 2>/dev/null)
if [[ -n "$UVICORN_PIDS" ]]; then
    echo "🌐 Stopping uvicorn processes on port 8000: $UVICORN_PIDS"
    kill $UVICORN_PIDS 2>/dev/null
fi

echo ""
echo "✅ All PDF Extractor Service processes stopped"
echo ""

# Optional: Show remaining Python processes
echo "📋 Remaining Python processes:"
pgrep -l python3 | head -5