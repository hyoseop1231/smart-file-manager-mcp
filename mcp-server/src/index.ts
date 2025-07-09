import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import axios from "axios";

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
            // Enable LLM categorization
            const enhancedArgs = { ...validatedArgs, use_llm: true };
            const response = await axios.post(`${AI_SERVICE_URL}/organize`, enhancedArgs);
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
            let endpoint = "";
            let payload: any = {};
            
            if (validatedArgs.category) {
              endpoint = `/category/${validatedArgs.category}`;
              payload = { limit: validatedArgs.limit };
            } else if (validatedArgs.extensions) {
              endpoint = "/extension";
              payload = validatedArgs.extensions;
            } else if (validatedArgs.recentHours) {
              endpoint = `/recent?hours=${validatedArgs.recentHours}&limit=${validatedArgs.limit}`;
            } else {
              throw new Error("Must specify category, extensions, or recentHours");
            }
            
            const response = await axios.get(`${AI_SERVICE_URL}${endpoint}`, {
              params: payload.limit ? { limit: payload.limit } : undefined,
              data: validatedArgs.extensions ? validatedArgs.extensions : undefined
            });
            
            return {
              content: [
                {
                  type: "text",
                  text: JSON.stringify(response.data, null, 2),
                },
              ],
            };
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