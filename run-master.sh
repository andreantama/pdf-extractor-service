#!/bin/bash

# Script untuk menjalankan hanya Master App (untuk development)

echo "🎯 Starting Master App Only (Development Mode)"
echo "=============================================="

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

# Create necessary directories
mkdir -p uploads temp logs

echo "🎯 Starting Master App..."
cd master_app
python main.py