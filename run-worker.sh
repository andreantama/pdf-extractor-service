#!/bin/bash

# Script untuk menjalankan hanya Worker App (untuk development)

echo "👷 Starting Worker App Only (Development Mode)"
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
mkdir -p logs

echo "👷 Starting Worker App..."
cd worker_app
python main.py