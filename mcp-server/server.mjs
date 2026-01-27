#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { ListToolsRequestSchema, CallToolRequestSchema, ListResourcesRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import axios from "axios";
import fs from "fs-extra";
import path from "path";

const API_BASE_URL = process.env.API_BASE_URL || "http://localhost:8001";
const NAS_PATH = "/home/hyoseop1231/nas_khs";

const server = new Server(
  { name: "smart-file-manager-mcp", version: "4.2.0" },
  { capabilities: { tools: {}, resources: {} } }
);

const api = axios.create({ baseURL: API_BASE_URL, timeout: 120000 });

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    // === 검색 ===
    { name: "search_files", description: "Search files by content, name, or AI analysis",
      inputSchema: { type: "object", properties: { query: { type: "string" }, media_types: { type: "array", items: { type: "string" } }, categories: { type: "array", items: { type: "string" } }, limit: { type: "number", default: 20 }, include_ai_analysis: { type: "boolean", default: false } }, required: ["query"] } },
    
    // === AI 분석 ===
    { name: "analyze_file", description: "Analyze file using Ollama Vision AI",
      inputSchema: { type: "object", properties: { file_path: { type: "string" }, analysis_type: { type: "string", enum: ["auto","image","video","audio","document"], default: "auto" }, force_reanalysis: { type: "boolean", default: false } }, required: ["file_path"] } },
    
    // === 파일 시스템 ===
    { name: "list_directory", description: "List files and folders in directory",
      inputSchema: { type: "object", properties: { path: { type: "string" }, recursive: { type: "boolean", default: false } }, required: ["path"] } },
    { name: "get_file_info", description: "Get detailed file information and metadata",
      inputSchema: { type: "object", properties: { file_path: { type: "string" } }, required: ["file_path"] } },
    { name: "move_file", description: "Move or rename file",
      inputSchema: { type: "object", properties: { source: { type: "string" }, destination: { type: "string" } }, required: ["source", "destination"] } },
    { name: "copy_file", description: "Copy file to new location",
      inputSchema: { type: "object", properties: { source: { type: "string" }, destination: { type: "string" } }, required: ["source", "destination"] } },
    { name: "delete_file", description: "Delete file (moves to trash)",
      inputSchema: { type: "object", properties: { file_path: { type: "string" }, permanent: { type: "boolean", default: false } }, required: ["file_path"] } },
    { name: "create_directory", description: "Create new directory",
      inputSchema: { type: "object", properties: { path: { type: "string" } }, required: ["path"] } },
    
    // === 파일 정리 ===
    { name: "organize_files", description: "AI-based file organization suggestions",
      inputSchema: { type: "object", properties: { directory: { type: "string" }, dry_run: { type: "boolean", default: true } }, required: ["directory"] } },
    { name: "find_duplicates", description: "Find duplicate files in directory",
      inputSchema: { type: "object", properties: { directory: { type: "string" }, by: { type: "string", enum: ["hash","name","size"], default: "hash" } }, required: ["directory"] } },
    { name: "categorize_files", description: "Categorize files by type/content",
      inputSchema: { type: "object", properties: { directory: { type: "string" } }, required: ["directory"] } },
    
    // === 디스크 관리 ===
    { name: "get_disk_usage", description: "Get disk usage statistics",
      inputSchema: { type: "object", properties: { path: { type: "string" } } } },
    { name: "get_disk_recommendations", description: "Get disk cleanup recommendations",
      inputSchema: { type: "object", properties: {} } },
    { name: "cleanup_thumbnails", description: "Clean old thumbnails",
      inputSchema: { type: "object", properties: { days: { type: "number", default: 30 } } } },
    { name: "cleanup_temp", description: "Clean temporary files",
      inputSchema: { type: "object", properties: {} } },
    
    // === 통계 ===
    { name: "get_system_stats", description: "Get system health and API status",
      inputSchema: { type: "object", properties: {} } },
    { name: "get_multimedia_stats", description: "Get multimedia file statistics",
      inputSchema: { type: "object", properties: {} } },
    
    // === 처리 상태 ===
    { name: "get_processing_status", description: "Get file processing status",
      inputSchema: { type: "object", properties: { file_id: { type: "string" } }, required: ["file_id"] } },
    { name: "reprocess_file", description: "Trigger file reprocessing",
      inputSchema: { type: "object", properties: { file_id: { type: "string" } }, required: ["file_id"] } },
    { name: "get_task_status", description: "Get background task status",
      inputSchema: { type: "object", properties: { task_id: { type: "string" } }, required: ["task_id"] } },
  ]
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  try {
    const result = await handleTool(name, args || {});
    return { content: [{ type: "text", text: typeof result === "string" ? result : JSON.stringify(result, null, 2) }] };
  } catch (e) {
    return { content: [{ type: "text", text: `Error: ${e.message}` }], isError: true };
  }
});

async function handleTool(name, args) {
  const resolvePath = (p) => p?.startsWith("/") ? p : path.join(NAS_PATH, p || "");
  
  switch (name) {
    // 검색
    case "search_files": {
      const res = await api.post("/search/multimedia", { query: args.query, media_types: args.media_types, categories: args.categories, limit: args.limit || 20, include_ai_analysis: args.include_ai_analysis });
      const r = res.data.results || [];
      return r.length ? r.map((f,i) => `${i+1}. ${f.name}\n   ${f.path}\n   ${f.media_type}/${f.category} | ${(f.size/1024/1024).toFixed(2)}MB`).join("\n\n") : "No files found";
    }
    // AI 분석
    case "analyze_file": {
      const res = await api.post("/ai/analyze", { file_path: args.file_path, analysis_type: args.analysis_type, force_reanalysis: args.force_reanalysis });
      return res.data;
    }
    // 파일 시스템
    case "list_directory": {
      const p = resolvePath(args.path);
      const items = await fs.readdir(p, { withFileTypes: true });
      return items.map(i => `${i.isDirectory()?"📁":"📄"} ${i.name}`).join("\n");
    }
    case "get_file_info": {
      const p = resolvePath(args.file_path);
      const s = await fs.stat(p);
      return { name: path.basename(p), path: p, size: s.size, sizeHuman: `${(s.size/1024/1024).toFixed(2)}MB`, modified: s.mtime, created: s.ctime, isDir: s.isDirectory() };
    }
    case "move_file": {
      await fs.move(resolvePath(args.source), resolvePath(args.destination));
      return `Moved: ${args.source} → ${args.destination}`;
    }
    case "copy_file": {
      await fs.copy(resolvePath(args.source), resolvePath(args.destination));
      return `Copied: ${args.source} → ${args.destination}`;
    }
    case "delete_file": {
      const p = resolvePath(args.file_path);
      if (args.permanent) await fs.remove(p);
      else await fs.move(p, path.join(NAS_PATH, ".trash", path.basename(p) + "_" + Date.now()));
      return `Deleted: ${args.file_path}`;
    }
    case "create_directory": {
      await fs.ensureDir(resolvePath(args.path));
      return `Created: ${args.path}`;
    }
    // 파일 정리
    case "organize_files": {
      const p = resolvePath(args.directory);
      const items = await fs.readdir(p, { withFileTypes: true });
      const files = items.filter(i => i.isFile());
      const cats = { images: [], documents: [], videos: [], audio: [], archives: [], others: [] };
      const extMap = { images: [".jpg",".jpeg",".png",".gif",".webp",".heic",".bmp",".svg",".tiff"], documents: [".pdf",".doc",".docx",".hwp",".hwpx",".txt",".md",".pptx",".ppt",".xlsx",".xls"], videos: [".mp4",".mov",".avi",".mkv",".webm",".wmv"], audio: [".mp3",".wav",".flac",".m4a",".aac",".ogg"], archives: [".zip",".tar",".gz",".rar",".7z"] };
      for (const f of files) {
        const ext = path.extname(f.name).toLowerCase();
        let found = false;
        for (const [cat, exts] of Object.entries(extMap)) { if (exts.includes(ext)) { cats[cat].push(f.name); found = true; break; } }
        if (!found) cats.others.push(f.name);
      }
      let out = `Organization for: ${p}\n\n`;
      for (const [c, list] of Object.entries(cats)) if (list.length) out += `📁 ${c}/ (${list.length})\n${list.slice(0,10).map(f=>"  - "+f).join("\n")}${list.length>10?"\n  ...":""}\n\n`;
      if (!args.dry_run) {
        let moved = 0;
        for (const [cat, list] of Object.entries(cats)) {
          if (list.length && cat !== "others") {
            const catDir = path.join(p, cat);
            await fs.ensureDir(catDir);
            for (const fname of list) {
              try { await fs.move(path.join(p, fname), path.join(catDir, fname), { overwrite: false }); moved++; } catch (e) {}
            }
          }
        }
        return out + `\n✅ Organized! Moved ${moved} files.`;
      }
      return out + "(Preview only)";
    }
    case "find_duplicates": {
      const p = resolvePath(args.directory);
      const items = await fs.readdir(p, { withFileTypes: true });
      const files = items.filter(i => i.isFile());
      const bySize = {};
      for (const f of files) { const s = (await fs.stat(path.join(p, f.name))).size; (bySize[s] = bySize[s] || []).push(f.name); }
      const dups = Object.entries(bySize).filter(([,v]) => v.length > 1).map(([sz, names]) => `Size ${sz}: ${names.join(", ")}`);
      return dups.length ? dups.join("\n") : "No duplicates found";
    }
    case "categorize_files": {
      return handleTool("organize_files", { directory: args.directory, dry_run: true });
    }
    // 디스크 관리
    case "get_disk_usage": {
      const res = await api.get("/disk/usage");
      return res.data;
    }
    case "get_disk_recommendations": {
      const res = await api.get("/disk/recommendations");
      return res.data;
    }
    case "cleanup_thumbnails": {
      const res = await api.post(`/disk/cleanup/thumbnails?days=${args.days || 30}`);
      return res.data;
    }
    case "cleanup_temp": {
      const res = await api.post("/disk/cleanup/temp");
      return res.data;
    }
    // 통계
    case "get_system_stats": {
      const res = await api.get("/health");
      return res.data;
    }
    case "get_multimedia_stats": {
      const res = await api.get("/stats/multimedia");
      return res.data;
    }
    // 처리 상태
    case "get_processing_status": {
      const res = await api.get(`/processing/status/${args.file_id}`);
      return res.data;
    }
    case "reprocess_file": {
      const res = await api.post(`/processing/reprocess/${args.file_id}`);
      return res.data;
    }
    case "get_task_status": {
      const res = await api.get(`/task/${args.task_id}`);
      return res.data;
    }
    default:
      throw new Error(`Unknown tool: ${name}`);
  }
}

server.setRequestHandler(ListResourcesRequestSchema, async () => ({ resources: [] }));
const transport = new StdioServerTransport();
await server.connect(transport);
console.error("Smart File Manager MCP v4.2.0 - All API features");
