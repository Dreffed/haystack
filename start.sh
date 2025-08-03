#!/bin/bash

# Haystack Docker Startup Script

echo "🕷️  Starting Haystack Web Collector Suite..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your settings before continuing!"
    echo "   Run: nano .env"
    echo "   Then run this script again."
    exit 1
fi

# Create required directories
echo "📁 Creating data directories..."
mkdir -p data/downloads data/haystack logs

# Start services
echo "🚀 Starting Docker services..."
docker-compose up -d

# Wait a moment for services to start
echo "⏳ Waiting for services to initialize..."
sleep 10

# Check service status
echo "📊 Checking service status..."
docker-compose ps

# Display access information
echo ""
echo "✅ Haystack is starting up!"
echo ""
echo "📱 Web Interface: http://localhost"
echo "🔧 API Documentation: http://localhost:8000/docs"
echo "📊 API Health Check: http://localhost:8000/health"
echo ""
echo "📝 To view logs: docker-compose logs -f"
echo "🛑 To stop: docker-compose down"
echo ""
echo "🎉 Happy scraping!"