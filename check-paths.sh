#!/bin/bash

echo "🔍 PDF Extractor Service - Directory Status"
echo "==========================================="

# Get current project root
PROJECT_ROOT=$(pwd)
echo "📁 Project Root: $PROJECT_ROOT"
echo ""

# Check directories
echo "📂 Directory Structure:"
echo "├── uploads/     $(if [ -d "uploads" ]; then echo "✅ EXISTS"; else echo "❌ NOT FOUND"; fi)"
echo "├── temp/        $(if [ -d "temp" ]; then echo "✅ EXISTS"; else echo "❌ NOT FOUND"; fi)"
echo "├── logs/        $(if [ -d "logs" ]; then echo "✅ EXISTS"; else echo "❌ NOT FOUND"; fi)"
echo "├── master_app/  $(if [ -d "master_app" ]; then echo "✅ EXISTS"; else echo "❌ NOT FOUND"; fi)"
echo "├── worker_app/  $(if [ -d "worker_app" ]; then echo "✅ EXISTS"; else echo "❌ NOT FOUND"; fi)"
echo "└── shared/      $(if [ -d "shared" ]; then echo "✅ EXISTS"; else echo "❌ NOT FOUND"; fi)"
echo ""

# Check if any files in uploads
if [ -d "uploads" ]; then
    FILE_COUNT=$(find uploads -name "*.pdf" | wc -l)
    echo "📄 Files in uploads/: $FILE_COUNT PDF files"
    if [ $FILE_COUNT -gt 0 ]; then
        echo "   Recent files:"
        find uploads -name "*.pdf" -printf "   - %f (%TY-%Tm-%Td %TH:%TM)\n" | head -5
    fi
else
    echo "📄 No uploads directory found"
fi
echo ""

# Check logs
if [ -d "logs" ]; then
    LOG_COUNT=$(find logs -name "*.log" | wc -l)
    echo "📋 Log files: $LOG_COUNT files"
    if [ $LOG_COUNT -gt 0 ]; then
        echo "   Available logs:"
        find logs -name "*.log" -printf "   - %f (%TY-%Tm-%Td %TH:%TM)\n"
    fi
else
    echo "📋 No logs directory found"
fi
echo ""

# Check if running from correct directory
if [ ! -f "master_app/main.py" ] || [ ! -f "worker_app/main.py" ]; then
    echo "⚠️  WARNING: Please run this script from the project root directory"
    echo "   Expected files not found. Current directory: $PROJECT_ROOT"
    echo ""
    echo "🔧 To fix:"
    echo "   cd /path/to/pdf-ekstractor-service"
    echo "   ./check-paths.sh"
else
    echo "✅ Running from correct project directory"
fi

echo ""
echo "🛠️  Path Configuration:"
echo "   Upload path will be: $PROJECT_ROOT/uploads/"
echo "   Temp path will be:   $PROJECT_ROOT/temp/"
echo "   Logs path will be:   $PROJECT_ROOT/logs/"