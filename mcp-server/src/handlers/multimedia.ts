import axios from "axios";
import { z } from "zod";
import {
  AnalyzeMediaVisionSchema,
  TranscribeMediaSchema,
  SearchMultimediaSchema,
  GenerateMediaPreviewSchema,
  OrganizeMediaSmartSchema,
  ExtractMediaContentSchema,
  MonitorMediaChangesSchema,
} from "../schemas/multimedia.js";

const API_BASE_URL = process.env.AI_SERVICE_URL || "http://localhost:8001";

// Helper function to handle API errors
function handleApiError(error: any, operation: string) {
  console.error(`[ERROR] ${operation} failed:`, error.message);
  if (error.response) {
    console.error(`[ERROR] Response:`, error.response.data);
    return {
      content: [{
        type: "text",
        text: `Error: ${operation} failed: ${error.response.data.detail || error.response.statusText}`
      }]
    };
  }
  return {
    content: [{
      type: "text",
      text: `Error: ${operation} failed: ${error.message}`
    }]
  };
}

// 1. Analyze Media Vision Handler
export async function analyzeMediaVision(args: unknown) {
  try {
    const params = AnalyzeMediaVisionSchema.parse(args);
    console.error(`[INFO] Analyzing media vision:`, params.filePath);

    const response = await axios.post(`${API_BASE_URL}/ai/analyze`, {
      file_path: params.filePath,
      analysis_type: params.analysisType === "text_ocr" ? "ocr" : params.analysisType,
      options: {
        language: params.language,
        video_options: params.videoOptions,
        comprehensive: params.analysisType === "comprehensive",
      }
    });

    const result = response.data;
    
    // Format the response for better readability
    let formattedContent = [];
    
    if (result.results?.image_analysis) {
      const analysis = result.results.image_analysis;
      formattedContent.push(`📸 Image Analysis:`);
      formattedContent.push(`Description: ${analysis.description}`);
      formattedContent.push(`Confidence: ${(analysis.confidence * 100).toFixed(1)}%`);
      
      if (analysis.metadata?.detected_objects) {
        formattedContent.push(`\nDetected Objects:`);
        analysis.metadata.detected_objects.forEach((obj: any) => {
          formattedContent.push(`  • ${obj.label} (${(obj.confidence * 100).toFixed(1)}%)`);
        });
      }
    }

    if (result.results?.ocr_text) {
      formattedContent.push(`\n📝 OCR Text Extraction:`);
      formattedContent.push(result.results.ocr_text);
    }

    if (result.results?.video_analysis) {
      formattedContent.push(`\n🎥 Video Analysis:`);
      formattedContent.push(`Frames analyzed: ${result.results.video_analysis.frames_analyzed}`);
      if (result.results.video_analysis.key_scenes) {
        formattedContent.push(`Key scenes: ${result.results.video_analysis.key_scenes.length}`);
      }
    }

    return {
      content: [{
        type: "text",
        text: formattedContent.join("\n") || "No analysis results available."
      }]
    };

  } catch (error) {
    return handleApiError(error, "Media vision analysis");
  }
}

// 2. Transcribe Media Handler
export async function transcribeMedia(args: unknown) {
  try {
    const params = TranscribeMediaSchema.parse(args);
    console.error(`[INFO] Transcribing media:`, params.filePath);

    const response = await axios.post(`${API_BASE_URL}/ai/transcribe`, {
      file_path: params.filePath,
      language: params.language,
      model: params.model,
      options: {
        include_timestamps: params.includeTimestamps,
        output_format: params.outputFormat,
        speaker_diarization: params.speakerDiarization,
      }
    });

    const result = response.data;
    let formattedContent = [];

    formattedContent.push(`🎙️ Transcription Results:`);
    formattedContent.push(`Language: ${result.language || params.language}`);
    formattedContent.push(`Duration: ${result.duration ? `${result.duration.toFixed(1)}s` : 'N/A'}`);
    formattedContent.push(`\n--- Transcript ---\n`);

    if (params.outputFormat === "json" && result.segments) {
      result.segments.forEach((segment: any) => {
        if (params.includeTimestamps) {
          formattedContent.push(`[${segment.start.toFixed(1)}s - ${segment.end.toFixed(1)}s]`);
        }
        if (params.speakerDiarization && segment.speaker) {
          formattedContent.push(`Speaker ${segment.speaker}: ${segment.text}`);
        } else {
          formattedContent.push(segment.text);
        }
      });
    } else {
      formattedContent.push(result.transcript || result.text || "No transcript available");
    }

    return {
      content: [{
        type: "text",
        text: formattedContent.join("\n")
      }]
    };

  } catch (error) {
    return handleApiError(error, "Media transcription");
  }
}

// 3. Search Multimedia Handler
export async function searchMultimedia(args: unknown) {
  try {
    const params = SearchMultimediaSchema.parse(args);
    console.error(`[INFO] Searching multimedia:`, params.query || "visual features");

    const searchParams: any = {
      query: params.query,
      media_types: params.mediaTypes.includes("all") ? ["image", "video", "audio"] : params.mediaTypes,
      limit: params.limit,
      search_mode: params.searchMode,
    };

    if (params.visualFeatures) {
      searchParams.visual_features = params.visualFeatures;
    }

    if (params.dateRange) {
      searchParams.date_range = params.dateRange;
    }

    const response = await axios.post(`${API_BASE_URL}/search/multimedia`, searchParams);
    const results = response.data.results || [];

    let formattedContent = [];
    formattedContent.push(`🔍 Multimedia Search Results:`);
    formattedContent.push(`Found: ${results.length} files`);
    formattedContent.push(`Search mode: ${params.searchMode}`);
    
    if (params.visualFeatures) {
      formattedContent.push(`Visual filters applied: ${Object.keys(params.visualFeatures).join(", ")}`);
    }

    formattedContent.push(`\n--- Results ---\n`);

    results.forEach((file: any, index: number) => {
      formattedContent.push(`${index + 1}. ${file.name || file.file_name}`);
      formattedContent.push(`   Path: ${file.path || file.file_path}`);
      formattedContent.push(`   Type: ${file.media_type || file.type}`);
      
      if (file.ai_analysis) {
        formattedContent.push(`   AI Tags: ${file.ai_analysis.tags?.join(", ") || "None"}`);
      }
      
      if (file.score) {
        formattedContent.push(`   Relevance: ${(file.score * 100).toFixed(1)}%`);
      }
      
      formattedContent.push("");
    });

    return {
      content: [{
        type: "text",
        text: formattedContent.join("\n")
      }]
    };

  } catch (error) {
    return handleApiError(error, "Multimedia search");
  }
}

// 4. Generate Media Preview Handler
export async function generateMediaPreview(args: unknown) {
  try {
    const params = GenerateMediaPreviewSchema.parse(args);
    console.error(`[INFO] Generating media preview:`, params.previewType);

    const response = await axios.post(`${API_BASE_URL}/media/preview`, {
      file_path: params.filePath,
      preview_type: params.previewType,
      options: params.options
    });

    const result = response.data;
    let formattedContent = [];

    formattedContent.push(`🖼️ Media Preview Generated:`);
    formattedContent.push(`Type: ${params.previewType}`);
    formattedContent.push(`Original file: ${params.filePath}`);
    
    if (result.preview_path) {
      formattedContent.push(`Preview saved to: ${result.preview_path}`);
    }

    if (result.thumbnail_url) {
      formattedContent.push(`Thumbnail URL: ${result.thumbnail_url}`);
    }

    if (params.previewType === "video_summary" && result.summary_info) {
      formattedContent.push(`\nVideo Summary:`);
      formattedContent.push(`Duration: ${result.summary_info.duration}s`);
      formattedContent.push(`Frames extracted: ${result.summary_info.frame_count}`);
      formattedContent.push(`File size: ${(result.summary_info.size_mb || 0).toFixed(2)} MB`);
    }

    if (params.previewType === "contact_sheet" && result.sheet_info) {
      formattedContent.push(`\nContact Sheet:`);
      formattedContent.push(`Grid: ${result.sheet_info.columns}x${result.sheet_info.rows}`);
      formattedContent.push(`Total frames: ${result.sheet_info.total_frames}`);
    }

    return {
      content: [{
        type: "text",
        text: formattedContent.join("\n")
      }]
    };

  } catch (error) {
    return handleApiError(error, "Preview generation");
  }
}

// 5. Organize Media Smart Handler
export async function organizeMediaSmart(args: unknown) {
  try {
    const params = OrganizeMediaSmartSchema.parse(args);
    console.error(`[INFO] Organizing media:`, params.organizationMethod);

    const response = await axios.post(`${API_BASE_URL}/organize/smart`, {
      source_dir: params.sourceDir,
      target_dir: params.targetDir || params.sourceDir,
      method: params.organizationMethod,
      options: {
        ...params.aiGrouping,
        preserve_originals: params.preserveOriginals,
        dry_run: params.dryRun,
      }
    });

    const result = response.data;
    let formattedContent = [];

    formattedContent.push(`📂 Smart Media Organization Results:`);
    formattedContent.push(`Method: ${params.organizationMethod}`);
    formattedContent.push(`Source: ${params.sourceDir}`);
    formattedContent.push(`Target: ${params.targetDir || params.sourceDir}`);
    formattedContent.push(`Mode: ${params.dryRun ? "Preview (Dry Run)" : "Actual Organization"}`);

    if (result.summary) {
      formattedContent.push(`\n📊 Summary:`);
      formattedContent.push(`Files processed: ${result.summary.total_files}`);
      formattedContent.push(`Groups created: ${result.summary.groups_created || 0}`);
      formattedContent.push(`Files organized: ${result.summary.files_organized || 0}`);
      
      if (params.organizationMethod === "duplicate_removal") {
        formattedContent.push(`Duplicates found: ${result.summary.duplicates_found || 0}`);
      }
    }

    if (result.groups && result.groups.length > 0) {
      formattedContent.push(`\n📁 Created Groups:`);
      result.groups.slice(0, 10).forEach((group: any) => {
        formattedContent.push(`\n• ${group.name} (${group.file_count} files)`);
        if (group.description) {
          formattedContent.push(`  Description: ${group.description}`);
        }
        if (group.sample_files) {
          formattedContent.push(`  Sample files:`);
          group.sample_files.slice(0, 3).forEach((file: string) => {
            formattedContent.push(`    - ${file}`);
          });
        }
      });
      
      if (result.groups.length > 10) {
        formattedContent.push(`\n... and ${result.groups.length - 10} more groups`);
      }
    }

    return {
      content: [{
        type: "text",
        text: formattedContent.join("\n")
      }]
    };

  } catch (error) {
    return handleApiError(error, "Smart media organization");
  }
}

// 6. Extract Media Content Handler
export async function extractMediaContent(args: unknown) {
  try {
    const params = ExtractMediaContentSchema.parse(args);
    console.error(`[INFO] Extracting media content:`, params.extractionType);

    const response = await axios.post(`${API_BASE_URL}/media/extract`, {
      file_path: params.filePath,
      extraction_types: params.extractionType,
      output_format: params.outputFormat,
      options: params.options
    });

    const result = response.data;
    let formattedContent = [];

    formattedContent.push(`📋 Media Content Extraction Results:`);
    formattedContent.push(`File: ${params.filePath}`);
    formattedContent.push(`Extraction types: ${params.extractionType.join(", ")}`);

    // Handle different extraction types
    if (params.extractionType.includes("metadata") && result.metadata) {
      formattedContent.push(`\n📊 Metadata:`);
      Object.entries(result.metadata).forEach(([key, value]) => {
        formattedContent.push(`  ${key}: ${value}`);
      });
    }

    if (params.extractionType.includes("text") && result.text) {
      formattedContent.push(`\n📝 Extracted Text:`);
      formattedContent.push(result.text.substring(0, 500) + (result.text.length > 500 ? "..." : ""));
    }

    if (params.extractionType.includes("faces") && result.faces) {
      formattedContent.push(`\n👤 Detected Faces: ${result.faces.count || 0}`);
      if (result.faces.details) {
        result.faces.details.slice(0, 5).forEach((face: any, index: number) => {
          formattedContent.push(`  Face ${index + 1}: ${face.confidence ? `${(face.confidence * 100).toFixed(1)}% confidence` : "detected"}`);
        });
      }
    }

    if (params.extractionType.includes("objects") && result.objects) {
      formattedContent.push(`\n🎯 Detected Objects:`);
      result.objects.slice(0, 10).forEach((obj: any) => {
        formattedContent.push(`  • ${obj.label} (${(obj.confidence * 100).toFixed(1)}%)`);
      });
    }

    if (params.extractionType.includes("subtitles") && result.subtitles) {
      formattedContent.push(`\n📺 Subtitles:`);
      formattedContent.push(`Format: ${result.subtitles.format || params.outputFormat}`);
      if (result.subtitles.preview) {
        formattedContent.push(`Preview: ${result.subtitles.preview.substring(0, 200)}...`);
      }
    }

    if (result.output_file) {
      formattedContent.push(`\n💾 Output saved to: ${result.output_file}`);
    }

    return {
      content: [{
        type: "text",
        text: formattedContent.join("\n")
      }]
    };

  } catch (error) {
    return handleApiError(error, "Media content extraction");
  }
}

// 7. Monitor Media Changes Handler
export async function monitorMediaChanges(args: unknown) {
  try {
    const params = MonitorMediaChangesSchema.parse(args);
    console.error(`[INFO] Setting up media monitoring:`, params.directories);

    const response = await axios.post(`${API_BASE_URL}/monitor/setup`, {
      directories: params.directories,
      auto_process: params.autoProcess,
      notifications: params.notifications,
      file_filters: params.fileFilters,
      schedule: params.schedule
    });

    const result = response.data;
    let formattedContent = [];

    formattedContent.push(`📡 Media Monitoring Setup:`);
    formattedContent.push(`Status: ${result.status || "Active"}`);
    formattedContent.push(`Monitor ID: ${result.monitor_id || "default"}`);
    
    formattedContent.push(`\n📁 Monitored Directories:`);
    params.directories.forEach(dir => {
      formattedContent.push(`  • ${dir}`);
    });

    formattedContent.push(`\n⚡ Auto-Processing Actions:`);
    params.autoProcess.forEach(action => {
      formattedContent.push(`  • ${action}`);
    });

    if (params.notifications) {
      formattedContent.push(`\n🔔 Notifications:`);
      if (params.notifications.onNewMedia) formattedContent.push(`  • New media files`);
      if (params.notifications.onDuplicates) formattedContent.push(`  • Duplicate files`);
      if (params.notifications.onLargeFiles) {
        formattedContent.push(`  • Large files (>${params.notifications.largeFileThresholdMB}MB)`);
      }
    }

    if (result.recent_activity) {
      formattedContent.push(`\n📊 Recent Activity:`);
      formattedContent.push(`Files processed: ${result.recent_activity.files_processed || 0}`);
      formattedContent.push(`New files detected: ${result.recent_activity.new_files || 0}`);
      formattedContent.push(`Duplicates found: ${result.recent_activity.duplicates || 0}`);
    }

    if (params.schedule?.enabled) {
      formattedContent.push(`\n⏰ Schedule:`);
      formattedContent.push(`Interval: Every ${params.schedule.intervalMinutes} minutes`);
      formattedContent.push(`Next run: ${result.next_run || "In " + params.schedule.intervalMinutes + " minutes"}`);
    }

    return {
      content: [{
        type: "text",
        text: formattedContent.join("\n")
      }]
    };

  } catch (error) {
    return handleApiError(error, "Media monitoring setup");
  }
}

// Export all handlers
export const MultimediaHandlers = {
  analyzeMediaVision,
  transcribeMedia,
  searchMultimedia,
  generateMediaPreview,
  organizeMediaSmart,
  extractMediaContent,
  monitorMediaChanges,
};