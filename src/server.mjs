#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import { execFileSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = process.env.PEANUT_OPENCLAW_ROOT || path.resolve(__dirname, "..");
const pythonBin = process.env.PEANUT_BRIDGE_PYTHON || path.join(repoRoot, ".venv", "bin", "python3");
const bridgeCli = path.join(repoRoot, "peanut_bridge", "cli.py");

function runBridge(action, payload = {}) {
  const out = execFileSync(pythonBin, [bridgeCli, action, JSON.stringify(payload)], {
    cwd: repoRoot,
    env: {
      ...process.env,
      PYTHONPATH: repoRoot,
    },
    encoding: "utf-8",
  });
  const parsed = JSON.parse(out);
  if (!parsed.ok) {
    throw new Error(parsed.error || "Bridge call failed");
  }
  return parsed.data;
}

const tools = [
  {
    name: "todo_create_task",
    description: "Create a Microsoft To Do task. Works as a generic tool, not command-only.",
    inputSchema: {
      type: "object",
      properties: {
        listName: { type: "string", default: "Personal" },
        title: { type: "string" },
        remind: { type: ["string", "null"], description: "YYYY-MM-DDTHH:MM:SS" },
        subTasks: { type: "array", items: { type: "string" }, default: [] }
      },
      required: ["title"]
    }
  },
  {
    name: "todo_set_my_day",
    description: "Add today's reminded tasks into My Day.",
    inputSchema: { type: "object", properties: {} }
  },
  {
    name: "note_save",
    description: "Save a note to MongoDB.",
    inputSchema: {
      type: "object",
      properties: {
        title: { type: "string" },
        content: { type: "string", default: "" },
        tags: { type: "array", items: { type: "string" }, default: [] }
      },
      required: ["title"]
    }
  },
  {
    name: "note_find",
    description: "Find notes by text query.",
    inputSchema: {
      type: "object",
      properties: {
        query: { type: "string" },
        tags: { type: "array", items: { type: "string" } }
      },
      required: ["query"]
    }
  },
  {
    name: "note_all",
    description: "List all notes sorted by updated time desc.",
    inputSchema: { type: "object", properties: {} }
  }
];

const server = new Server(
  {
    name: "peanut-mcp",
    version: "0.1.0"
  },
  {
    capabilities: {
      tools: {}
    }
  }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools }));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const name = request.params.name;
  const args = request.params.arguments || {};

  if (!tools.find((t) => t.name === name)) {
    throw new Error(`Unknown tool: ${name}`);
  }

  const data = runBridge(name, args);
  return {
    content: [
      {
        type: "text",
        text: JSON.stringify(data, null, 2)
      }
    ]
  };
});

const transport = new StdioServerTransport();
await server.connect(transport);
