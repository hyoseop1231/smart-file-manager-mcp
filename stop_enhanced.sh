#!/bin/bash

echo "🛑 Stopping Enhanced Smart File Manager..."

# Stop indexer
if [ -f /tmp/smart-file-manager-indexer.pid ]; then
    INDEXER_PID=$(cat /tmp/smart-file-manager-indexer.pid)
    if ps -p $INDEXER_PID > /dev/null; then
        kill $INDEXER_PID
        echo "✓ Stopped indexer (PID: $INDEXER_PID)"
    fi
    rm /tmp/smart-file-manager-indexer.pid
fi

# Stop API
if [ -f /tmp/smart-file-manager-api.pid ]; then
    API_PID=$(cat /tmp/smart-file-manager-api.pid)
    if ps -p $API_PID > /dev/null; then
        kill $API_PID
        echo "✓ Stopped API server (PID: $API_PID)"
    fi
    rm /tmp/smart-file-manager-api.pid
fi

echo "✅ Enhanced Smart File Manager stopped"