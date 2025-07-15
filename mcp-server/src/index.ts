import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import axios from "axios";

// Import multimedia schemas and handlers
import {
  AnalyzeMediaVisionSchema,
  TranscribeMediaSchema,
  SearchMultimediaSchema,
  GenerateMediaPreviewSchema,
  OrganizeMediaSmartSchema,
  ExtractMediaContentSchema,
  MonitorMediaChangesSchema,
} from "./schemas/multimedia.js";

import {
  analyzeMediaVision,
  transcribeMedia,
  searchMultimedia,
  generateMediaPreview,
  organizeMediaSmart,
  extractMediaContent,
  monitorMediaChanges,
} from "./handlers/multimedia.js";

// Tool schemas
const SearchFilesSchema = z.object({
  query: z.string().describe("Search query in natural language"),
  directories: z.array(z.string()).optional().describe("Directories to search in"),
  language: z.string().optional().default("ko").describe("Language for search"),
  limit: z.number().optional().default(10).describe("Maximum number of results"),
}).transform((data) => ({
  ...data,
  // Ensure directories is always an array or undefined
  directories: data.directories && data.directories.length > 0 ? data.directories : undefined,
}));

const QuickSearchSchema = z.object({
  category: z.enum(["image", "video", "audio", "document", "code", "archive", "other"]).optional(),
  extensions: z.array(z.string()).optional(),
  recentHours: z.number().optional(),
  limit: z.number().optional().default(50),
});

const OrganizeFilesSchema = z.object({
  sourceDir: z.string().describe("Source directory to organize"),
  targetDir: z.string().optional().describe("Target directory for organized files"),
  method: z.enum(["content", "date", "type"]).describe("Organization method"),
  dryRun: z.boolean().optional().default(false).describe("Preview mode without actual changes"),
});

const SmartWorkflowSchema = z.object({
  searchQuery: z.string().describe("Search query to find files"),
  action: z.enum(["organize", "analyze", "rename"]).describe("Action to perform on found files"),
  options: z.record(z.any()).optional().describe("Additional options for the action"),
});

const AnalyzeFileSchema = z.object({
  filePath: z.string().describe("Path to the file to analyze"),
  analysisType: z.enum(["content", "metadata", "vision", "smart"]).optional().default("smart").describe("Type of analysis to perform"),
});

const SystemStatusSchema = z.object({
  detailed: z.boolean().optional().default(false).describe("Get detailed system metrics"),
});

const FindDuplicatesSchema = z.object({
  directories: z.array(z.string()).optional().describe("Directories to search for duplicates"),
  method: z.enum(["hash", "name", "size", "content"]).optional().default("hash").describe("Duplicate detection method"),
  minSize: z.number().optional().default(0).describe("Minimum file size to consider"),
});

const BatchOperationSchema = z.object({
  operation: z.enum(["rename", "move", "copy", "delete"]).describe("Batch operation to perform"),
  files: z.array(z.string()).describe("List of file paths to operate on"),
  options: z.record(z.any()).optional().describe("Operation-specific options"),
});

// AI Service URL (will be set by environment variable)
const AI_SERVICE_URL = process.env.AI_SERVICE_URL || "http://localhost:8001";

class SmartFileManagerServer {
  private server: Server;

  constructor() {
    this.server = new Server(
      {
        name: "smart-file-manager-mcp",
        version: "1.0.0",
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupHandlers();
  }

  private setupHandlers() {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: "search_files",
          description: "Search files using indexed database (fast) or AI-powered semantic search",
          inputSchema: {
            type: "object",
            properties: {
              query: { type: "string", description: "Search query in natural language" },
              directories: { 
                type: "array", 
                items: { type: "string" },
                description: "Directories to search in (optional)"
              },
              language: { type: "string", description: "Language for search (default: ko)" },
              limit: { type: "number", description: "Maximum number of results (default: 10)" },
            },
            required: ["query"],
          },
        },
        {
          name: "quick_search",
          description: "Quick file search by category, extension, or recent files (database only)",
          inputSchema: {
            type: "object",
            properties: {
              category: { 
                type: "string", 
                enum: ["image", "video", "audio", "document", "code", "archive", "other"],
                description: "File category to search"
              },
              extensions: { 
                type: "array", 
                items: { type: "string" },
                description: "File extensions to search (e.g., ['.pdf', '.docx'])"
              },
              recentHours: { 
                type: "number", 
                description: "Find files modified in the last N hours"
              },
              limit: { type: "number", description: "Maximum number of results (default: 50)" },
            },
          },
        },
        {
          name: "organize_files",
          description: "Organize files using AI-powered categorization",
          inputSchema: {
            type: "object",
            properties: {
              sourceDir: { type: "string", description: "Source directory to organize" },
              targetDir: { type: "string", description: "Target directory for organized files" },
              method: { 
                type: "string", 
                enum: ["content", "date", "type"],
                description: "Organization method"
              },
              dryRun: { type: "boolean", description: "Preview mode without actual changes" },
            },
            required: ["sourceDir", "method"],
          },
        },
        {
          name: "smart_workflow",
          description: "Combine search and organization in one workflow",
          inputSchema: {
            type: "object",
            properties: {
              searchQuery: { type: "string", description: "Search query to find files" },
              action: { 
                type: "string",
                enum: ["organize", "analyze", "rename"],
                description: "Action to perform on found files"
              },
              options: { type: "object", description: "Additional options for the action" },
            },
            required: ["searchQuery", "action"],
          },
        },
        {
          name: "analyze_file",
          description: "Analyze a specific file using AI (content, metadata, vision, or smart selection)",
          inputSchema: {
            type: "object",
            properties: {
              filePath: { type: "string", description: "Path to the file to analyze" },
              analysisType: { 
                type: "string",
                enum: ["content", "metadata", "vision", "smart"],
                description: "Type of analysis to perform (default: smart)"
              },
            },
            required: ["filePath"],
          },
        },
        {
          name: "system_status",
          description: "Get system health, indexing status, and performance metrics",
          inputSchema: {
            type: "object",
            properties: {
              detailed: { type: "boolean", description: "Get detailed system metrics (default: false)" },
            },
          },
        },
        {
          name: "find_duplicates",
          description: "Find duplicate files using various detection methods",
          inputSchema: {
            type: "object",
            properties: {
              directories: { 
                type: "array",
                items: { type: "string" },
                description: "Directories to search for duplicates"
              },
              method: { 
                type: "string",
                enum: ["hash", "name", "size", "content"],
                description: "Duplicate detection method (default: hash)"
              },
              minSize: { type: "number", description: "Minimum file size to consider (default: 0)" },
            },
          },
        },
        {
          name: "batch_operation",
          description: "Perform batch operations on multiple files (rename, move, copy, delete)",
          inputSchema: {
            type: "object",
            properties: {
              operation: { 
                type: "string",
                enum: ["rename", "move", "copy", "delete"],
                description: "Batch operation to perform"
              },
              files: { 
                type: "array",
                items: { type: "string" },
                description: "List of file paths to operate on"
              },
              options: { type: "object", description: "Operation-specific options" },
            },
            required: ["operation", "files"],
          },
        },
        {
          name: "analyze_media_vision",
          description: "Analyze images and videos using AI vision (OCR, object detection, scene analysis, face detection)",
          inputSchema: {
            type: "object",
            properties: {
              filePath: { type: "string", description: "Path to the media file to analyze" },
              analysisType: { 
                type: "string", 
                enum: ["caption", "objects", "scene", "text_ocr", "face_detection", "comprehensive"],
                description: "Type of AI vision analysis (default: comprehensive)"
              },
              videoOptions: { 
                type: "object",
                properties: {
                  frameInterval: { type: "number", description: "Analyze every N frames (default: 30)" },
                  maxFrames: { type: "number", description: "Maximum frames to analyze (default: 10)" },
                  keyFramesOnly: { type: "boolean", description: "Analyze only key frames (default: true)" }
                }
              },
              language: { type: "string", description: "Language for OCR and descriptions (default: auto)" },
            },
            required: ["filePath"],
          },
        },
        {
          name: "transcribe_media",
          description: "Transcribe audio and video files to text using AI speech recognition",
          inputSchema: {
            type: "object",
            properties: {
              filePath: { type: "string", description: "Path to audio/video file to transcribe" },
              language: { 
                type: "string", 
                enum: ["auto", "ko", "en", "ja", "zh", "es", "fr", "de", "ru"],
                description: "Language of the audio (default: auto)"
              },
              model: { 
                type: "string", 
                enum: ["tiny", "base", "small", "medium", "large"],
                description: "Whisper model size (default: base)"
              },
              includeTimestamps: { type: "boolean", description: "Include timestamps in transcript (default: false)" },
              outputFormat: { 
                type: "string", 
                enum: ["text", "srt", "vtt", "json"],
                description: "Output format for transcription (default: text)"
              },
              speakerDiarization: { type: "boolean", description: "Identify different speakers (default: false)" },
            },
            required: ["filePath"],
          },
        },
        {
          name: "search_multimedia",
          description: "Search for multimedia files using semantic search, visual similarity, transcripts, or AI tags",
          inputSchema: {
            type: "object",
            properties: {
              query: { type: "string", description: "Text search query" },
              searchMode: { 
                type: "string", 
                enum: ["semantic", "visual_similarity", "transcript", "ai_tags", "comprehensive"],
                description: "Search mode (default: comprehensive)"
              },
              mediaTypes: { 
                type: "array", 
                items: { type: "string", enum: ["image", "video", "audio", "all"] },
                description: "Media types to search (default: all)"
              },
              visualFeatures: { 
                type: "object",
                properties: {
                  colors: { type: "array", items: { type: "string" }, description: "Dominant colors to search" },
                  objects: { type: "array", items: { type: "string" }, description: "Objects to find in images" },
                  scenes: { type: "array", items: { type: "string" }, description: "Scene types (indoor, outdoor, etc)" },
                  faces: { type: "number", description: "Number of faces to look for" }
                }
              },
              dateRange: { 
                type: "object",
                properties: {
                  start: { type: "string", description: "Start date (ISO format)" },
                  end: { type: "string", description: "End date (ISO format)" }
                }
              },
              limit: { type: "number", description: "Maximum results (default: 20)" },
            },
          },
        },
        {
          name: "generate_media_preview",
          description: "Generate thumbnails, animated GIFs, video summaries, or contact sheets for media files",
          inputSchema: {
            type: "object",
            properties: {
              filePath: { type: "string", description: "Path to media file" },
              previewType: { 
                type: "string", 
                enum: ["thumbnail", "animated_gif", "video_summary", "audio_waveform", "contact_sheet"],
                description: "Type of preview to generate"
              },
              options: { 
                type: "object",
                properties: {
                  size: { type: "string", enum: ["small", "medium", "large", "custom"], description: "Preview size (default: medium)" },
                  customSize: { 
                    type: "object",
                    properties: {
                      width: { type: "number" },
                      height: { type: "number" }
                    }
                  },
                  format: { type: "string", enum: ["jpeg", "png", "webp", "gif"], description: "Output format (default: jpeg)" },
                  quality: { type: "number", description: "Quality 1-100 (default: 85)" },
                  duration: { type: "number", description: "Duration in seconds for video summaries" },
                  fps: { type: "number", description: "Frames per second for GIFs (default: 10)" },
                  columns: { type: "number", description: "Columns for contact sheets (default: 4)" },
                  rows: { type: "number", description: "Rows for contact sheets (default: 3)" }
                }
              },
            },
            required: ["filePath", "previewType"],
          },
        },
        {
          name: "organize_media_smart",
          description: "Organize media files intelligently using AI-powered grouping by faces, scenes, events, or quality",
          inputSchema: {
            type: "object",
            properties: {
              sourceDir: { type: "string", description: "Source directory containing media" },
              targetDir: { type: "string", description: "Target directory for organized files" },
              organizationMethod: { 
                type: "string", 
                enum: ["faces", "scenes", "events", "ai_categories", "quality", "duplicate_removal", "date_location", "content_type"],
                description: "Organization method"
              },
              aiGrouping: { 
                type: "object",
                properties: {
                  groupSimilar: { type: "boolean", description: "Group visually similar media (default: true)" },
                  createAlbums: { type: "boolean", description: "Create album folders (default: true)" },
                  detectEvents: { type: "boolean", description: "Detect and group by events (default: true)" },
                  similarityThreshold: { type: "number", description: "Similarity threshold 0-1 (default: 0.8)" },
                  minGroupSize: { type: "number", description: "Minimum files for a group (default: 3)" }
                }
              },
              preserveOriginals: { type: "boolean", description: "Keep original files (default: true)" },
              dryRun: { type: "boolean", description: "Preview without moving files (default: false)" },
            },
            required: ["sourceDir", "organizationMethod"],
          },
        },
        {
          name: "extract_media_content",
          description: "Extract text, faces, objects, landmarks, metadata, subtitles, or frames from media files",
          inputSchema: {
            type: "object",
            properties: {
              filePath: { type: "string", description: "Path to media file" },
              extractionType: { 
                type: "array", 
                items: { 
                  type: "string", 
                  enum: ["text", "faces", "objects", "landmarks", "metadata", "subtitles", "audio", "frames"] 
                },
                description: "Types of content to extract"
              },
              outputFormat: { 
                type: "string", 
                enum: ["json", "text", "srt", "vtt", "csv"],
                description: "Output format (default: json)"
              },
              options: { 
                type: "object",
                properties: {
                  frameCount: { type: "number", description: "Number of frames to extract (default: 10)" },
                  includeThumbnails: { type: "boolean", description: "Include thumbnails (default: true)" },
                  faceRecognition: { type: "boolean", description: "Enable face recognition (default: false)" },
                  objectConfidence: { type: "number", description: "Object detection confidence 0-1 (default: 0.5)" }
                }
              },
            },
            required: ["filePath", "extractionType"],
          },
        },
        {
          name: "monitor_media_changes",
          description: "Monitor directories for new media files and auto-process them (index, thumbnail, transcribe, analyze)",
          inputSchema: {
            type: "object",
            properties: {
              directories: { 
                type: "array", 
                items: { type: "string" },
                description: "Directories to monitor"
              },
              autoProcess: { 
                type: "array", 
                items: { 
                  type: "string", 
                  enum: ["index", "thumbnail", "transcribe", "analyze", "organize"] 
                },
                description: "Auto-processing actions (default: index, thumbnail)"
              },
              notifications: { 
                type: "object",
                properties: {
                  onNewMedia: { type: "boolean", description: "Notify on new media (default: true)" },
                  onDuplicates: { type: "boolean", description: "Notify on duplicates (default: true)" },
                  onLargeFiles: { type: "boolean", description: "Notify on large files (default: true)" },
                  largeFileThresholdMB: { type: "number", description: "Large file threshold in MB (default: 100)" }
                }
              },
              fileFilters: { 
                type: "object",
                properties: {
                  extensions: { type: "array", items: { type: "string" } },
                  minSizeMB: { type: "number" },
                  maxSizeMB: { type: "number" }
                }
              },
              schedule: { 
                type: "object",
                properties: {
                  enabled: { type: "boolean", description: "Enable scheduled processing (default: false)" },
                  intervalMinutes: { type: "number", description: "Processing interval in minutes (default: 60)" }
                }
              },
            },
            required: ["directories"],
          },
        },
      ],
    }));

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      try {
        const { name, arguments: args } = request.params;

        switch (name) {
          case "search_files": {
            try {
              console.error(`[DEBUG] Raw search_files args:`, JSON.stringify(args));
              const validatedArgs = SearchFilesSchema.parse(args);
              console.error(`[DEBUG] Validated search_files args:`, JSON.stringify(validatedArgs));
              
              // Add LLM enhancement flag for semantic search
              const enhancedArgs = { ...validatedArgs, use_llm: true };
              console.error(`[DEBUG] Enhanced args for AI service:`, JSON.stringify(enhancedArgs));
              
              // Try the fixed search endpoint first
              try {
                const response = await axios.post(`${AI_SERVICE_URL}/search`, enhancedArgs, {
                  headers: { 'Content-Type': 'application/json' },
                  timeout: 30000
                });
                
                console.error(`[DEBUG] Search response received:`, response.status);
                
                return {
                  content: [
                    {
                      type: "text",
                      text: JSON.stringify(response.data, null, 2),
                    },
                  ],
                };
              } catch (mainError) {
                console.error(`[ERROR] Main search endpoint failed:`, mainError);
                
                // Log detailed error information
                if (axios.isAxiosError(mainError)) {
                  console.error(`[ERROR] Response status:`, mainError.response?.status);
                  console.error(`[ERROR] Response data:`, JSON.stringify(mainError.response?.data, null, 2));
                  console.error(`[ERROR] Response headers:`, mainError.response?.headers);
                }
                
                // Fallback to simple search endpoint
                try {
                  console.error(`[DEBUG] Trying fallback search_simple endpoint`);
                  const fallbackResponse = await axios.post(`${AI_SERVICE_URL}/search_simple`, enhancedArgs, {
                    headers: { 'Content-Type': 'application/json' },
                    timeout: 30000
                  });
                  
                  console.error(`[DEBUG] Fallback search response received:`, fallbackResponse.status);
                  
                  return {
                    content: [
                      {
                        type: "text",
                        text: JSON.stringify(fallbackResponse.data, null, 2),
                      },
                    ],
                  };
                } catch (fallbackError) {
                  console.error(`[ERROR] Fallback search also failed:`, fallbackError);
                  
                  if (axios.isAxiosError(fallbackError)) {
                    console.error(`[ERROR] Fallback response status:`, fallbackError.response?.status);
                    console.error(`[ERROR] Fallback response data:`, JSON.stringify(fallbackError.response?.data, null, 2));
                  }
                  
                  throw mainError; // Throw the original error
                }
              }
            } catch (error) {
              console.error(`[ERROR] search_files validation or processing failed:`, error);
              
              if (axios.isAxiosError(error)) {
                console.error(`[ERROR] Axios error details:`, {
                  status: error.response?.status,
                  statusText: error.response?.statusText,
                  data: error.response?.data,
                  config: {
                    url: error.config?.url,
                    method: error.config?.method,
                    headers: error.config?.headers,
                    data: error.config?.data
                  }
                });
              }
              
              throw error;
            }
          }

          case "organize_files": {
            const validatedArgs = OrganizeFilesSchema.parse(args);
            
            // Map method names to match API expectations
            const methodMap = {
              "content": "content",
              "date": "date", 
              "type": "extension"
            };
            
            const organizeArgs = {
              sourceDir: validatedArgs.sourceDir,
              targetDir: validatedArgs.targetDir,
              method: methodMap[validatedArgs.method] || validatedArgs.method,
              dryRun: validatedArgs.dryRun || false,
              use_llm: validatedArgs.method === "content" ? true : false  // Only use LLM for content organization
            };
            
            const response = await axios.post(`${AI_SERVICE_URL}/organize`, organizeArgs);
            return {
              content: [
                {
                  type: "text",
                  text: JSON.stringify(response.data, null, 2),
                },
              ],
            };
          }

          case "smart_workflow": {
            const validatedArgs = SmartWorkflowSchema.parse(args);
            
            // smart_workflow combines search and organize
            if (validatedArgs.action === "organize") {
              // First search for files
              const searchArgs = {
                query: validatedArgs.searchQuery,
                use_llm: true,
                limit: 100
              };
              
              // Convert organize options to correct format
              const organizeArgs = {
                sourceDir: validatedArgs.options?.sourceDir || "/watch_directories/Desktop",
                targetDir: validatedArgs.options?.targetDir || "/watch_directories/Desktop/Organized",
                method: validatedArgs.options?.method || "content",
                dryRun: validatedArgs.options?.dryRun || false,
                use_llm: true,
                createStructure: validatedArgs.options?.createStructure || true,
                preserveExisting: validatedArgs.options?.preserveExisting || true
              };
              
              const response = await axios.post(`${AI_SERVICE_URL}/organize`, organizeArgs);
              return {
                content: [
                  {
                    type: "text",
                    text: JSON.stringify(response.data, null, 2),
                  },
                ],
              };
            } else if (validatedArgs.action === "analyze") {
              // For analyze, use search endpoint
              const searchArgs = {
                query: validatedArgs.searchQuery,
                use_llm: true,
                limit: 50
              };
              
              const response = await axios.post(`${AI_SERVICE_URL}/search`, searchArgs);
              return {
                content: [
                  {
                    type: "text",
                    text: JSON.stringify(response.data, null, 2),
                  },
                ],
              };
            } else {
              throw new Error(`Action ${validatedArgs.action} not supported yet`);
            }
          }

          case "quick_search": {
            const validatedArgs = QuickSearchSchema.parse(args);
            
            // Convert quick_search to regular search with appropriate query
            let searchQuery = "";
            let searchArgs: any = {
              use_llm: false,  // Quick search doesn't need LLM
              limit: validatedArgs.limit || 50
            };
            
            if (validatedArgs.category) {
              // Map category to search query
              const categoryMap = {
                "image": "type:image OR extension:.jpg OR extension:.png OR extension:.gif OR extension:.jpeg OR extension:.svg",
                "video": "type:video OR extension:.mp4 OR extension:.avi OR extension:.mov OR extension:.mkv",
                "audio": "type:audio OR extension:.mp3 OR extension:.wav OR extension:.flac OR extension:.aac",
                "document": "type:document OR extension:.pdf OR extension:.doc OR extension:.docx OR extension:.txt OR extension:.md",
                "code": "type:code OR extension:.py OR extension:.js OR extension:.java OR extension:.cpp OR extension:.html OR extension:.css",
                "archive": "type:archive OR extension:.zip OR extension:.rar OR extension:.7z OR extension:.tar OR extension:.gz",
                "other": "type:other"
              };
              searchQuery = categoryMap[validatedArgs.category] || `category:${validatedArgs.category}`;
            } else if (validatedArgs.extensions) {
              // Convert extensions to search query
              searchQuery = validatedArgs.extensions.map(ext => `extension:${ext}`).join(" OR ");
            } else if (validatedArgs.recentHours) {
              // Use the /recent endpoint for recent files
              const response = await axios.get(`${AI_SERVICE_URL}/recent`, {
                params: {
                  hours: validatedArgs.recentHours,
                  limit: validatedArgs.limit || 50
                }
              });
              
              return {
                content: [
                  {
                    type: "text",
                    text: JSON.stringify(response.data, null, 2),
                  },
                ],
              };
            } else {
              throw new Error("Must specify category, extensions, or recentHours");
            }
            
            // Use search endpoint for category and extension searches
            searchArgs.query = searchQuery;
            const response = await axios.post(`${AI_SERVICE_URL}/search`, searchArgs);
            
            return {
              content: [
                {
                  type: "text",
                  text: JSON.stringify(response.data, null, 2),
                },
              ],
            };
          }

          case "analyze_file": {
            const validatedArgs = AnalyzeFileSchema.parse(args);
            
            // Convert file path to container path
            const containerPath = validatedArgs.filePath.replace("/Users/hyoseop1231", "/watch_directories");
            
            // Use the new /analyze endpoint
            const analyzeArgs = {
              filePath: containerPath,
              analysisType: validatedArgs.analysisType
            };
            
            const response = await axios.post(`${AI_SERVICE_URL}/analyze`, analyzeArgs);
            
            return {
              content: [
                {
                  type: "text",
                  text: JSON.stringify(response.data, null, 2),
                },
              ],
            };
          }

          case "system_status": {
            const validatedArgs = SystemStatusSchema.parse(args);
            
            // Get health and metrics
            const [healthResponse, metricsResponse] = await Promise.all([
              axios.get(`${AI_SERVICE_URL}/health`),
              validatedArgs.detailed ? axios.get(`${AI_SERVICE_URL}/metrics`) : Promise.resolve(null)
            ]);
            
            const result = {
              health: healthResponse.data,
              metrics: metricsResponse?.data || "Use detailed:true for full metrics"
            };
            
            return {
              content: [
                {
                  type: "text",
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case "find_duplicates": {
            const validatedArgs = FindDuplicatesSchema.parse(args);
            
            // Use the new /duplicates endpoint
            const duplicateArgs = {
              method: validatedArgs.method,
              minSize: validatedArgs.minSize,
              directories: validatedArgs.directories
            };
            
            const response = await axios.post(`${AI_SERVICE_URL}/duplicates`, duplicateArgs);
            
            return {
              content: [
                {
                  type: "text",
                  text: JSON.stringify(response.data, null, 2),
                },
              ],
            };
          }

          case "batch_operation": {
            const validatedArgs = BatchOperationSchema.parse(args);
            
            // For now, return a preview of what would be done
            // In a real implementation, this would perform the actual operations
            const result = {
              operation: validatedArgs.operation,
              files_count: validatedArgs.files.length,
              files: validatedArgs.files,
              options: validatedArgs.options,
              status: "preview_mode",
              note: "This is a preview. Actual batch operations would require additional safety checks and implementation."
            };
            
            return {
              content: [
                {
                  type: "text",
                  text: JSON.stringify(result, null, 2),
                },
              ],
            };
          }

          case "analyze_media_vision": {
            const validatedArgs = AnalyzeMediaVisionSchema.parse(args);
            return await analyzeMediaVision(validatedArgs);
          }

          case "transcribe_media": {
            const validatedArgs = TranscribeMediaSchema.parse(args);
            return await transcribeMedia(validatedArgs);
          }

          case "search_multimedia": {
            const validatedArgs = SearchMultimediaSchema.parse(args);
            return await searchMultimedia(validatedArgs);
          }

          case "generate_media_preview": {
            const validatedArgs = GenerateMediaPreviewSchema.parse(args);
            return await generateMediaPreview(validatedArgs);
          }

          case "organize_media_smart": {
            const validatedArgs = OrganizeMediaSmartSchema.parse(args);
            return await organizeMediaSmart(validatedArgs);
          }

          case "extract_media_content": {
            const validatedArgs = ExtractMediaContentSchema.parse(args);
            return await extractMediaContent(validatedArgs);
          }

          case "monitor_media_changes": {
            const validatedArgs = MonitorMediaChangesSchema.parse(args);
            return await monitorMediaChanges(validatedArgs);
          }

          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        return {
          content: [
            {
              type: "text",
              text: `Error: ${error instanceof Error ? error.message : String(error)}`,
            },
          ],
        };
      }
    });
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    // Log to stderr to avoid interfering with JSON-RPC communication
    console.error("Smart File Manager MCP Server running...");
  }
}

// Start the server
const server = new SmartFileManagerServer();
server.run().catch(console.error);