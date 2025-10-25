#!/bin/bash

# Script untuk menjalankan PDF Extractor Service secara lokal

echo "🚀 Starting PDF Extractor Service..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install docker-compose first."
    exit 1
fi

echo "📋 Building and starting services..."

# Build and start services
docker-compose up --build -d

echo "⏳ Waiting for services to be ready..."

# Wait for master app to be ready
echo "Checking master app health..."
for i in {1..30}; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Master app is ready!"
        break
    fi
    echo "Waiting... ($i/30)"
    sleep 2
done

# Check if services are running
echo ""
echo "📊 Service Status:"
echo "===================="

if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Master App: Running (http://localhost:8000)"
else
    echo "❌ Master App: Not responding"
fi

if docker-compose ps | grep -q "redis.*Up"; then
    echo "✅ Redis: Running"
else
    echo "❌ Redis: Not running"
fi

WORKER_COUNT=$(docker-compose ps | grep worker | grep Up | wc -l)
echo "✅ Workers: $WORKER_COUNT running"

echo ""
echo "🎉 PDF Extractor Service is ready!"
echo ""
echo "📖 API Documentation: http://localhost:8000/docs"
echo "🔍 Health Check: http://localhost:8000/health"
echo ""
echo "To stop the service, run: docker-compose down"
echo "To view logs, run: docker-compose logs -f"