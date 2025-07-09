#!/bin/bash
# Quick organize script with status checking

echo "🗂️ Starting file organization..."

# Start organization
RESPONSE=$(curl -s -X POST http://localhost:8001/organize \
  -H "Content-Type: application/json" \
  -d '{
    "sourceDir": "/watch_directories/Desktop",
    "targetDir": "/watch_directories/Desktop/Organized",
    "method": "extension",
    "dryRun": true,
    "use_llm": false
  }')

# Extract task ID if it's a background task
TASK_ID=$(echo $RESPONSE | grep -o '"task_id":"[^"]*' | cut -d'"' -f4)

if [ -n "$TASK_ID" ]; then
    echo "Task started with ID: $TASK_ID"
    echo "Waiting for completion..."
    
    # Wait and check status
    for i in {1..30}; do
        STATUS=$(curl -s http://localhost:8001/task/$TASK_ID | grep -o '"status":"[^"]*' | cut -d'"' -f4)
        
        if [ "$STATUS" = "completed" ]; then
            echo "✅ Organization complete!"
            curl -s http://localhost:8001/task/$TASK_ID | jq '.results'
            break
        elif [ "$STATUS" = "failed" ]; then
            echo "❌ Organization failed"
            curl -s http://localhost:8001/task/$TASK_ID | jq '.error'
            break
        else
            echo -n "."
            sleep 1
        fi
    done
else
    # Direct response (no LLM)
    echo "✅ Organization complete!"
    echo $RESPONSE | jq '.results'
fi