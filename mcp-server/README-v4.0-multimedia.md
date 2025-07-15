# Smart File Manager MCP Server v4.0 - Multimedia Edition

## 🚀 What's New in v4.0

The Smart File Manager MCP Server v4.0 introduces **7 powerful multimedia processing tools** that bring advanced AI-powered media capabilities directly to Claude Desktop:

### 🎯 New Multimedia Tools

1. **analyze_media_vision** - AI vision analysis for images and videos
   - OCR text extraction from images
   - Object detection and scene analysis
   - Face detection and counting
   - Comprehensive image captioning
   - Video frame analysis

2. **transcribe_media** - AI-powered speech-to-text
   - Support for audio and video files
   - Multi-language support (Korean, English, Japanese, Chinese, etc.)
   - Multiple Whisper model sizes
   - Timestamp and speaker diarization options
   - Multiple output formats (text, SRT, VTT, JSON)

3. **search_multimedia** - Advanced multimedia search
   - Semantic search across media files
   - Visual similarity search
   - Search by transcript content
   - Search by AI-generated tags
   - Visual feature filters (colors, objects, scenes, faces)

4. **generate_media_preview** - Smart preview generation
   - Thumbnails for images and videos
   - Animated GIFs from videos
   - Video summaries
   - Audio waveforms
   - Contact sheets for video collections

5. **organize_media_smart** - AI-powered media organization
   - Group by detected faces
   - Organize by scene types
   - Event detection and grouping
   - Quality-based organization
   - Duplicate removal
   - Content-type categorization

6. **extract_media_content** - Content extraction
   - Extract text from images (OCR)
   - Face extraction and recognition
   - Object detection and extraction
   - Landmark detection
   - Metadata extraction
   - Subtitle extraction from videos
   - Frame extraction

7. **monitor_media_changes** - Real-time media monitoring
   - Watch directories for new media
   - Auto-process new files (index, thumbnail, transcribe, analyze)
   - Duplicate detection notifications
   - Large file alerts
   - Scheduled processing

## 🎮 Usage Examples

### Analyze an Image with AI Vision
```
User: Use analyze_media_vision to analyze the screenshot at /Users/me/Desktop/screenshot.png

Claude: I'll analyze that screenshot using AI vision analysis.

[Uses analyze_media_vision tool]

📸 Image Analysis:
Description: A screenshot showing a code editor with Python code for a machine learning model
Confidence: 92.3%

Detected Objects:
  • Text editor (95.1%)
  • Code snippet (93.7%)
  • Python syntax (89.2%)

📝 OCR Text Extraction:
import tensorflow as tf
from tensorflow import keras
...
```

### Transcribe a Video
```
User: Transcribe the meeting recording at /Users/me/Videos/meeting.mp4 in Korean

Claude: I'll transcribe that meeting recording in Korean.

[Uses transcribe_media tool]

🎙️ Transcription Results:
Language: ko
Duration: 1523.4s

--- Transcript ---
안녕하세요, 오늘 회의를 시작하겠습니다...
```

### Search for Similar Images
```
User: Find all images similar to my vacation photo that have beaches and sunset

Claude: I'll search for images with beaches and sunsets similar to your vacation photo.

[Uses search_multimedia tool]

🔍 Multimedia Search Results:
Found: 24 files
Search mode: visual_similarity
Visual filters applied: scenes, colors

--- Results ---
1. sunset_beach_2023.jpg
   Path: /Users/me/Pictures/Vacation/sunset_beach_2023.jpg
   Type: image
   AI Tags: beach, sunset, ocean, golden hour
   Relevance: 94.2%
...
```

### Organize Photos by Faces
```
User: Organize my family photos by detected faces

Claude: I'll organize your family photos by grouping them based on detected faces.

[Uses organize_media_smart tool]

📂 Smart Media Organization Results:
Method: faces
Source: /Users/me/Pictures/Family
Mode: Actual Organization

📊 Summary:
Files processed: 842
Groups created: 12
Files organized: 837

📁 Created Groups:
• Person_1 (156 files)
  Description: Most frequent person, appears in group photos
• Person_2 (98 files)  
  Description: Second most frequent, often with Person_1
...
```

## 🔧 Installation

1. **Build the MCP Server**
   ```bash
   cd /path/to/smart-file-manager-mcp/mcp-server
   npm install
   npm run build
   ```

2. **Update Claude Desktop Configuration**
   
   Edit your Claude Desktop MCP configuration file:
   ```json
   {
     "smart-file-manager": {
       "command": "node",
       "args": ["/path/to/smart-file-manager-mcp/mcp-server/dist/index.js"],
       "env": {
         "AI_SERVICE_URL": "http://localhost:8001"
       }
     }
   }
   ```

3. **Start the AI Service**
   ```bash
   cd /path/to/smart-file-manager-mcp
   docker-compose -f docker-compose-multimedia-v4.yml up -d
   ```

4. **Restart Claude Desktop**
   
   Quit and restart Claude Desktop to load the new multimedia tools.

## 🐳 Docker Services

The v4.0 system includes several Docker services:

- **smart-file-manager-v4**: Main AI service with multimedia processing
- **qdrant**: Vector database for semantic search
- **mcp-server-v4**: MCP server for Claude Desktop
- **web-ui-v4**: Web dashboard with multimedia preview
- **redis**: Caching and job queues
- **prometheus**: Monitoring and metrics

## 📋 Requirements

- Docker and Docker Compose
- Node.js 18+ for MCP server
- 4GB+ RAM recommended for multimedia processing
- FFmpeg (included in Docker image)
- Tesseract OCR (included in Docker image)

## 🔍 Troubleshooting

1. **Tools not appearing in Claude Desktop**
   - Ensure the MCP server is built: `npm run build`
   - Check Claude Desktop logs for errors
   - Verify AI_SERVICE_URL is correct in config

2. **Multimedia processing errors**
   - Check if Docker services are running: `docker-compose ps`
   - View logs: `docker-compose logs smart-file-manager-v4`
   - Ensure sufficient memory allocated to Docker

3. **Slow processing**
   - First-time AI model downloads may take time
   - Check Docker resource limits
   - Consider using smaller Whisper models for faster transcription

## 🎯 Best Practices

1. **For Large Media Collections**
   - Use `dryRun: true` first to preview organization changes
   - Process in batches to avoid memory issues
   - Enable monitoring for automatic processing

2. **For Accuracy**
   - Use `comprehensive` analysis type for best results
   - Specify language explicitly for better transcription
   - Use higher similarity thresholds for face grouping

3. **For Performance**
   - Use specific search modes instead of `comprehensive`
   - Limit frame analysis for long videos
   - Enable caching for repeated operations

## 🚀 What's Next

Future enhancements planned:
- Real-time video stream analysis
- Advanced face recognition with names
- Music and audio analysis
- 3D media support
- Cloud storage integration