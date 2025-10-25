#!/bin/bash

# Script untuk setup development environment

echo "🔧 Setting up PDF Extractor Service for local development..."
echo "========================================================="

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "📍 Detected Python version: $PYTHON_VERSION"

if [[ ! "$PYTHON_VERSION" =~ ^3\.(11|12)\. ]]; then
    echo "⚠️  Warning: This project is tested with Python 3.11+ and 3.12.x"
    echo "   Current version: $PYTHON_VERSION"
    read -p "   Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
if [[ ! -d "venv" ]]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source myenv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

if [[ $? -eq 0 ]]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p uploads temp logs
echo "✅ Directories created"

# Copy environment file
if [[ ! -f ".env" ]]; then
    echo "⚙️  Creating .env file..."
    cp .env.example .env
    echo "✅ .env file created from template"
else
    echo "✅ .env file already exists"
fi

# Check for Redis
echo "🔍 Checking Redis availability..."
if command -v redis-server &> /dev/null; then
    echo "✅ Redis server found"
else
    echo "⚠️  Redis server not found. You have options:"
    echo "   1. Install Redis locally: sudo apt install redis-server (Ubuntu/Debian)"
    echo "   2. Use Docker Redis: docker run -d -p 6379:6379 redis:7-alpine"
    echo "   3. Use existing Redis instance (update .env file)"
fi

# Check tesseract
echo "🔍 Checking Tesseract OCR..."
if command -v tesseract &> /dev/null; then
    TESSERACT_VERSION=$(tesseract --version 2>&1 | head -n1)
    echo "✅ $TESSERACT_VERSION"
else
    echo "⚠️  Tesseract OCR not found. Install with:"
    echo "   Ubuntu/Debian: sudo apt install tesseract-ocr tesseract-ocr-eng tesseract-ocr-ind"
    echo "   macOS: brew install tesseract"
fi

echo ""
echo "🎉 Setup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Start Redis server (if not using Docker)"
echo "2. Run: source venv/bin/activate"
echo "3. Run: ./run-local.sh"
echo ""
echo "📖 See README.md for detailed instructions"