# Continuity local MCP demo

This project includes a read-only MCP server, `mcp_server.py`, backed only by synthetic evidence in `data/demo_records.json`. It exposes three deliberately narrow tools:

- `list_sources` — discover available records
- `search_evidence` — retrieve likely evidence for a question
- `get_evidence` — read one record by its stable chunk ID

## Run locally

Install the project dependencies, including the MCP SDK:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Then use the server through any MCP client configured to start a Python stdio process:

```powershell
.\.venv\Scripts\python.exe mcp_server.py
```

Keep it read-only for demonstrations. No production credentials, customer data, or write tools are included.

## Connect to Codex

Codex can register HTTP MCP servers with `codex mcp add <name> --url <url>` and list them with `codex mcp list`. For a private or local MCP server, configure it using the client’s stdio-server settings and point it to the Python executable and this project’s `mcp_server.py`.

For the public OpenAI documentation MCP, the official Codex command is:

```powershell
codex mcp add openaiDeveloperDocs --url https://developers.openai.com/mcp
codex mcp list
```

OpenAI’s MCP guidance distinguishes service-reachable HTTP servers from environment-connected HTTP or stdio servers. A local server must run in the same environment as the agent, and credentials should be supplied through a protected environment or trusted proxy—not stored in source files.

## Production path

Replace synthetic retrieval one source at a time: GitHub first, then Jira, SharePoint, and email. For each connector, use least-privilege, read-only credentials; expose only `search` and `get` tools initially; and retain source identifiers, timestamps, and access-control metadata in every result.
