#!/bin/bash

# Smart File Manager - Web UI Startup Script
echo "🚀 Starting Smart File Manager Web UI..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+ first."
    echo "   Visit: https://nodejs.org/"
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt "16" ]; then
    echo "❌ Node.js version 16+ required. Current version: $(node -v)"
    exit 1
fi

# Check if we're in the correct directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Please run this script from the smart-file-manager-mcp root directory"
    exit 1
fi

echo "✅ Node.js $(node -v) detected"

# Check if the API service is running
echo "🔍 Checking if Smart File Manager API is running..."
if curl -f -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "✅ API service is running on port 8001"
else
    echo "⚠️  API service not detected on port 8001"
    echo "   Starting Docker services first..."
    
    docker-compose up -d smart-file-manager
    
    echo "   Waiting for API service to be ready..."
    for i in {1..30}; do
        if curl -f -s http://localhost:8001/health > /dev/null 2>&1; then
            echo "✅ API service is now ready!"
            break
        fi
        echo -n "."
        sleep 2
    done
    
    if ! curl -f -s http://localhost:8001/health > /dev/null 2>&1; then
        echo "❌ Failed to start API service. Please check Docker logs:"
        echo "   docker logs smart-file-manager"
        exit 1
    fi
fi

# Navigate to web-ui directory
cd web-ui

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies"
        exit 1
    fi
    echo "✅ Dependencies installed successfully"
else
    echo "✅ Dependencies already installed"
fi

# Start the development server
echo "🌐 Starting Web UI development server..."
echo ""
echo "📍 Web UI will be available at: http://localhost:3002"
echo "📍 API service is running at: http://localhost:8001"
echo ""
echo "🎯 Features available:"
echo "   • 📊 Dashboard - System monitoring and analytics"
echo "   • 🗂️  File Explorer - AI-powered search and browse"
echo "   • 📈 Analytics - Duplicate detection and insights"
echo "   • 🤖 Organization - AI file organization wizard"
echo "   • ⚙️  Settings - System configuration"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the React development server on port 3002
PORT=3002 npm start