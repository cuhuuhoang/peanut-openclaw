#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = process.env.PEANUT_OPENCLAW_ROOT || path.resolve(__dirname, "..");
const pythonBin = process.env.PEANUT_BRIDGE_PYTHON || path.join(repoRoot, ".venv", "bin", "python3");
const bridgeCli = path.join(repoRoot, "peanut_bridge", "cli.py");

function runBridge(action, payload = {}) {
  const proc = spawnSync(pythonBin, [bridgeCli, action, JSON.stringify(payload)], {
    cwd: repoRoot,
    env: {
      ...process.env,
      PYTHONPATH: repoRoot,
    },
    encoding: "utf-8",
  });

  const stdout = (proc.stdout || "").trim();
  const stderr = (proc.stderr || "").trim();

  if (!stdout) {
    return {
      ok: false,
      error: stderr || `Bridge produced no output (exit ${proc.status ?? "unknown"})`,
    };
  }

  try {
    return JSON.parse(stdout);
  } catch {
    return {
      ok: false,
      error: `Invalid bridge JSON: ${stdout}${stderr ? ` | stderr: ${stderr}` : ""}`,
    };
  }
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
  },
  {
    name: "funix_extract_session_from_url",
    description: "Extract FUNiX session details from portal URL.",
    inputSchema: {
      type: "object",
      properties: {
        url: { type: "string" }
      },
      required: ["url"]
    }
  },
  {
    name: "funix_create_todo_from_url",
    description: "Extract FUNiX session and create To Do reminder.",
    inputSchema: {
      type: "object",
      properties: {
        url: { type: "string" },
        listName: { type: "string", default: "Funix" }
      },
      required: ["url"]
    }
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

  const result = runBridge(name, args);
  if (!result.ok) {
    return {
      isError: true,
      content: [
        {
          type: "text",
          text: JSON.stringify({ error: result.error }, null, 2)
        }
      ]
    };
  }

  return {
    content: [
      {
        type: "text",
        text: JSON.stringify(result.data, null, 2)
      }
    ]
  };
});

const transport = new StdioServerTransport();
await server.connect(transport);
