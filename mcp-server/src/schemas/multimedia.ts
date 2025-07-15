import { z } from "zod";

// 1. AI Vision Analysis Schema
export const AnalyzeMediaVisionSchema = z.object({
  filePath: z.string().describe("Path to the media file to analyze"),
  analysisType: z.enum([
    "caption",
    "objects", 
    "scene",
    "text_ocr",
    "face_detection",
    "comprehensive"
  ]).optional().default("comprehensive").describe("Type of AI vision analysis"),
  videoOptions: z.object({
    frameInterval: z.number().optional().default(30).describe("Analyze every N frames"),
    maxFrames: z.number().optional().default(10).describe("Maximum frames to analyze"),
    keyFramesOnly: z.boolean().optional().default(true).describe("Analyze only key frames"),
  }).optional(),
  language: z.string().optional().default("auto").describe("Language for OCR and descriptions"),
});

// 2. Media Transcription Schema  
export const TranscribeMediaSchema = z.object({
  filePath: z.string().describe("Path to audio/video file to transcribe"),
  language: z.enum([
    "auto", "ko", "en", "ja", "zh", "es", "fr", "de", "ru"
  ]).optional().default("auto").describe("Language of the audio"),
  model: z.enum([
    "tiny", "base", "small", "medium", "large"
  ]).optional().default("base").describe("Whisper model size"),
  includeTimestamps: z.boolean().optional().default(false).describe("Include timestamps in transcript"),
  outputFormat: z.enum([
    "text", "srt", "vtt", "json"
  ]).optional().default("text").describe("Output format for transcription"),
  speakerDiarization: z.boolean().optional().default(false).describe("Identify different speakers"),
});

// 3. Enhanced Multimedia Search Schema
export const SearchMultimediaSchema = z.object({
  query: z.string().optional().describe("Text search query"),
  searchMode: z.enum([
    "semantic", "visual_similarity", "transcript", "ai_tags", "comprehensive"
  ]).optional().default("comprehensive").describe("Search mode"),
  mediaTypes: z.array(z.enum([
    "image", "video", "audio", "all"
  ])).optional().default(["all"]).describe("Media types to search"),
  visualFeatures: z.object({
    colors: z.array(z.string()).optional().describe("Dominant colors to search"),
    objects: z.array(z.string()).optional().describe("Objects to find in images"),
    scenes: z.array(z.string()).optional().describe("Scene types (indoor, outdoor, etc)"),
    faces: z.number().optional().describe("Number of faces to look for"),
  }).optional(),
  dateRange: z.object({
    start: z.string().optional().describe("Start date (ISO format)"),
    end: z.string().optional().describe("End date (ISO format)"),
  }).optional(),
  limit: z.number().optional().default(20).describe("Maximum results"),
});

// 4. Media Preview Generation Schema
export const GenerateMediaPreviewSchema = z.object({
  filePath: z.string().describe("Path to media file"),
  previewType: z.enum([
    "thumbnail", "animated_gif", "video_summary", "audio_waveform", "contact_sheet"
  ]).describe("Type of preview to generate"),
  options: z.object({
    size: z.enum(["small", "medium", "large", "custom"]).optional().default("medium"),
    customSize: z.object({
      width: z.number(),
      height: z.number(),
    }).optional(),
    format: z.enum(["jpeg", "png", "webp", "gif"]).optional().default("jpeg"),
    quality: z.number().min(1).max(100).optional().default(85),
    duration: z.number().optional().describe("Duration in seconds for video summaries"),
    fps: z.number().optional().default(10).describe("Frames per second for GIFs"),
    columns: z.number().optional().default(4).describe("Columns for contact sheets"),
    rows: z.number().optional().default(3).describe("Rows for contact sheets"),
  }).optional(),
});

// 5. Smart Media Organization Schema
export const OrganizeMediaSmartSchema = z.object({
  sourceDir: z.string().describe("Source directory containing media"),
  targetDir: z.string().optional().describe("Target directory for organized files"),
  organizationMethod: z.enum([
    "faces", "scenes", "events", "ai_categories", 
    "quality", "duplicate_removal", "date_location", "content_type"
  ]).describe("Organization method"),
  aiGrouping: z.object({
    groupSimilar: z.boolean().optional().default(true).describe("Group visually similar media"),
    createAlbums: z.boolean().optional().default(true).describe("Create album folders"),
    detectEvents: z.boolean().optional().default(true).describe("Detect and group by events"),
    similarityThreshold: z.number().min(0).max(1).optional().default(0.8),
    minGroupSize: z.number().optional().default(3).describe("Minimum files for a group"),
  }).optional(),
  preserveOriginals: z.boolean().optional().default(true).describe("Keep original files"),
  dryRun: z.boolean().optional().default(false).describe("Preview without moving files"),
});

// 6. Media Content Extraction Schema
export const ExtractMediaContentSchema = z.object({
  filePath: z.string().describe("Path to media file"),
  extractionType: z.array(z.enum([
    "text", "faces", "objects", "landmarks", 
    "metadata", "subtitles", "audio", "frames"
  ])).describe("Types of content to extract"),
  outputFormat: z.enum([
    "json", "text", "srt", "vtt", "csv"
  ]).optional().default("json").describe("Output format"),
  options: z.object({
    frameCount: z.number().optional().default(10).describe("Number of frames to extract"),
    includeThumbnails: z.boolean().optional().default(true),
    faceRecognition: z.boolean().optional().default(false),
    objectConfidence: z.number().min(0).max(1).optional().default(0.5),
  }).optional(),
});

// 7. Media Monitoring Schema
export const MonitorMediaChangesSchema = z.object({
  directories: z.array(z.string()).describe("Directories to monitor"),
  autoProcess: z.array(z.enum([
    "index", "thumbnail", "transcribe", "analyze", "organize"
  ])).optional().default(["index", "thumbnail"]).describe("Auto-processing actions"),
  notifications: z.object({
    onNewMedia: z.boolean().optional().default(true),
    onDuplicates: z.boolean().optional().default(true),
    onLargeFiles: z.boolean().optional().default(true),
    largeFileThresholdMB: z.number().optional().default(100),
  }).optional(),
  fileFilters: z.object({
    extensions: z.array(z.string()).optional(),
    minSizeMB: z.number().optional(),
    maxSizeMB: z.number().optional(),
  }).optional(),
  schedule: z.object({
    enabled: z.boolean().optional().default(false),
    intervalMinutes: z.number().optional().default(60),
  }).optional(),
});

// Export all schemas
export const MultimediaSchemas = {
  AnalyzeMediaVisionSchema,
  TranscribeMediaSchema,
  SearchMultimediaSchema,
  GenerateMediaPreviewSchema,
  OrganizeMediaSmartSchema,
  ExtractMediaContentSchema,
  MonitorMediaChangesSchema,
};