#!/bin/bash

# Enhanced Smart File Manager Startup Script
# Includes MAFM Multi-Agent + Local-File-Organizer features

echo "🚀 Starting Enhanced Smart File Manager..."

# Check if Ollama is running
if ! pgrep -x "ollama" > /dev/null; then
    echo "⚠️  Ollama is not running. Starting Ollama..."
    ollama serve &
    sleep 5
fi

# Check required models
echo "🔍 Checking Ollama models..."
if ! ollama list | grep -q "llama3.2:3b"; then
    echo "📥 Downloading llama3.2:3b model..."
    ollama pull llama3.2:3b
fi

if ! ollama list | grep -q "llava:7b"; then
    echo "📥 Downloading llava:7b vision model..."
    ollama pull llava:7b
fi

# Create necessary directories
mkdir -p /tmp/smart-file-manager/{db,embeddings,metadata,organized}

# Start the indexer in background
echo "📇 Starting background indexer..."
cd /Users/hyoseop1231/AI_Coding/smart-file-manager-mcp
python ai-services/indexer.py &
INDEXER_PID=$!
echo "Indexer PID: $INDEXER_PID"

# Start the enhanced API
echo "🌐 Starting enhanced API server..."
cd ai-services
python enhanced_api.py &
API_PID=$!
echo "API PID: $API_PID"

# Save PIDs for later
echo $INDEXER_PID > /tmp/smart-file-manager-indexer.pid
echo $API_PID > /tmp/smart-file-manager-api.pid

echo "✅ Enhanced Smart File Manager is running!"
echo "📍 API URL: http://localhost:8001"
echo "🤖 Ollama URL: http://localhost:11434"
echo ""
echo "Features enabled:"
echo "  ✓ Multi-Agent Search (MAFM)"
echo "  ✓ LLM File Organization (Local-File-Organizer)"
echo "  ✓ Semantic Search with Embeddings"
echo "  ✓ Background Indexing"
echo "  ✓ Smart Workflows"
echo ""
echo "To stop: ./stop_enhanced.sh"