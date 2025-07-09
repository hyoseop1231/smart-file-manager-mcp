#!/bin/bash

# Smart File Manager Deployment Script
# This script sets up and deploys the Smart File Manager system

set -e

echo "🚀 Smart File Manager Deployment Script"
echo "========================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from example..."
    cp .env.example .env
    echo "✅ .env file created. Please review and customize it before continuing."
    echo "   Key settings to check:"
    echo "   - Directory paths (HOME_DOCUMENTS, HOME_DOWNLOADS, etc.)"
    echo "   - GPU support (ENABLE_GPU)"
    echo "   - Supervisor credentials"
    echo ""
    read -p "Press Enter to continue after reviewing .env file..."
fi

# Source environment variables
source .env

echo "🔧 Setting up Ollama models..."
echo "This may take a while on first run..."

# Start Ollama service first
echo "🐳 Starting Ollama service..."
docker-compose up -d ollama

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama to be ready..."
sleep 30

# Pull required models
echo "📦 Pulling required LLM models..."
docker-compose exec ollama ollama pull qwen2.5:3b
docker-compose exec ollama ollama pull llava:13b
docker-compose exec ollama ollama pull nomic-embed-text

echo "✅ Ollama models ready"

# Build and start all services
echo "🏗️ Building and starting all services..."
docker-compose up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Health check
echo "🔍 Checking service health..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -f http://localhost:${PORT}/health &> /dev/null; then
        echo "✅ Smart File Manager is healthy!"
        break
    fi
    
    attempt=$((attempt + 1))
    echo "⏳ Attempt $attempt/$max_attempts - waiting for service..."
    sleep 5
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Service failed to start properly. Check logs:"
    echo "   docker-compose logs smart-file-manager"
    exit 1
fi

# Display connection info
echo ""
echo "🎉 Deployment successful!"
echo "========================"
echo "📊 Service URLs:"
echo "   - Smart File Manager API: http://localhost:${PORT}"
echo "   - Supervisor Interface: http://localhost:${SUPERVISOR_PORT}"
echo "   - Ollama API: http://localhost:${OLLAMA_PORT}"
echo ""
echo "📋 Useful commands:"
echo "   - View logs: docker-compose logs -f"
echo "   - Stop services: docker-compose down"
echo "   - Restart services: docker-compose restart"
echo "   - Health check: curl http://localhost:${PORT}/health"
echo ""
echo "🔧 Claude Desktop Configuration:"
echo "   Add this to your Claude Desktop MCP settings:"
echo "   {"
echo "     \"smart-file-manager\": {"
echo "       \"command\": \"node\","
echo "       \"args\": [\"$(pwd)/mcp-server/dist/index.js\"],"
echo "       \"env\": {"
echo "         \"AI_SERVICE_URL\": \"http://localhost:${PORT}\""
echo "       }"
echo "     }"
echo "   }"

echo ""
echo "🎯 Next steps:"
echo "   1. Add the MCP configuration to Claude Desktop"
echo "   2. Restart Claude Desktop"
echo "   3. Test with: '파일 찾아줘' or 'find files'"
echo ""
echo "📚 Documentation: Check README.md for detailed usage instructions"