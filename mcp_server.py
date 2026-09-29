"""Read-only local MCP server for Continuity's synthetic evidence corpus."""

from __future__ import annotations

import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP


DATA_PATH = Path(__file__).parent / "data" / "demo_records.json"
server = FastMCP("continuity-demo-evidence")


def records() -> list[dict]:
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


@server.tool()
def list_sources() -> list[dict]:
    """List the synthetic evidence sources available to Continuity."""
    return [
        {"chunk_id": item["chunk_id"], "source": item["source_file"], "type": item["source_type"], "entity": item["entity"]}
        for item in records()
    ]


@server.tool()
def search_evidence(query: str, limit: int = 5) -> list[dict]:
    """Search synthetic evidence by matching query terms against source metadata and text."""
    terms = {term.lower() for term in query.split() if len(term) > 2}
    ranked = []
    for item in records():
        searchable = " ".join([item["source_file"], item["section_title"], item["entity"], item["text"], *item["keywords"]]).lower()
        score = sum(term in searchable for term in terms)
        if score:
            ranked.append((score, item))
    return [item for _, item in sorted(ranked, key=lambda pair: pair[0], reverse=True)[:max(1, min(limit, 10))]]


@server.tool()
def get_evidence(chunk_id: str) -> dict:
    """Return one synthetic evidence record by its stable chunk ID."""
    for item in records():
        if item["chunk_id"] == chunk_id:
            return item
    return {"error": f"No evidence record exists for {chunk_id}."}


if __name__ == "__main__":
    server.run(transport="stdio")
