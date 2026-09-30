# Legacy Context Continuity Assistant

A local MVP for the modernization-focused internal knowledge assistant described in the design document. It is intentionally scoped to a demoable, evidence-first workflow that highlights:

- conflict detection between documentation and current code
- documentation gap detection when knowledge is missing or stale
- transparent source-backed answers instead of unsupported model memory

## Project structure

- `app.py` — Streamlit UI
- `knowledge_assistant/core.py` — seed data, answer logic, conflict and gap handling
- `tests/test_knowledge_assistant.py` — validation tests

## Quick start

### Windows PowerShell

```powershell
cd "c:\Users\sparsha.srinath\NET projects\CoSD\AI Fullstack\Modernization Assistant"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
streamlit run app.py
```

### Or use the helper script

```powershell
cd "c:\Users\sparsha.srinath\NET projects\CoSD\AI Fullstack\Modernization Assistant"
./run_app.ps1
```

## Demo scenarios

On the `demo` branch, launch the live modernization studio with:

```powershell
./run_demo.ps1 -Install # First run; installs dependencies
./run_demo.ps1          # Subsequent runs
```

The demo opens on port 8502 with four views: Overview, Knowledge base,
Chunk explorer, and Live Q&A. Add or edit evidence, preview and change chunk
boundaries, generate answers with the configured model, and pin before/after
comparisons. Clear the KB or restore its baseline in one click.

Each browser session owns an isolated, in-memory Chroma index. Edits and
answer history last for that session (not across a browser reload or server
restart); original source files and the normal persistent KB stay intact.
Export documents before ending a session if you need a copy. New uploads
support UTF-8 text, Markdown, Python, SQL, CSV, and JSON (500 KB per document).
The baseline also ingests its existing Excel records.

**Document library** lists all indexed source documents with version, type,
chunk count, and path. **Import codebase** previews ZIP archives or multiple
source files and indexes a reviewed batch together. ZIPs retain folder paths;
repeat imports update matching paths in the same codebase/version. Limits:
20 MB uploaded, 10 MB expanded text, 500 files per batch, 500 KB per file.
Dependencies, build output, binary files, and common credential filenames are
skipped with reasons visible in the preview.

All answers use live retrieval and model generation; there are no prepared
answers. Configure a provider below for Q&A. Evidence editing and chunk
exploration work without a running model. See [the live presenter workflow](docs/presenter-demo.md).

## Synthetic data and MCP demo

The app now uses a structured, synthetic evidence corpus in `data/demo_records.json`. It represents policy, ticket, code, email, runbook, and compliance records without connecting to real systems.

`mcp_server.py` exposes that corpus through a read-only local MCP server. See [`docs/mcp-local-demo.md`](docs/mcp-local-demo.md) for setup, tool scope, and the safe production rollout path.

## BLPTS versioned corpus

The assistant recursively ingests non-empty documentation, code, SQL, email, CSV, and Excel files from `blpts_legacy/` and `blpts_mod/` at startup. Legacy chunks receive `system_version=legacy`; modernized chunks receive `system_version=mod_v1`. Excel worksheets are extracted into text for indexing. The Q&A panel's retrieval-scope selector supports Legacy only, Modernized only, and Compare both.

## Local model options

The checked-in local setting uses `qwen2.5:3b`, the smallest installed generation model. For more reliable JSON and citation selection, use `qwen3:4b` (about 2.5 GB) as the quality/latency default, or `qwen3:8b` (about 5.2 GB) when the machine has enough memory. Ollama lists both variants and their context windows in its [Qwen3 model catalog](https://ollama.com/library/qwen3/tags). Install one with `ollama pull qwen3:4b` (or `qwen3:8b`), then set `LLM_MODEL` in `.streamlit/secrets.toml` to the same tag. `gemma3:4b` is another 3.3 GB option with a 128K context window.

The related Jira issues were created in the connected `KAN` project: discovery `KAN-4` and `KAN-5`, modernization `KAN-6` and `KAN-7`. The inspection discovery ticket has the County Clerk's resolution recorded as a comment. The modernization tickets are unassigned because K. Ibarra could not be found as an assignable Jira user; the requested assignee is retained in each issue description.

## Verification

### Retrieval and generation diagnostics

Answers are generated from retrieved passages; there are no question-specific answers or factual fallbacks. Long records are split at paragraph/line boundaries (up to 1,800 characters) and ranked using BM25 over content, titles and filenames. Chroma's hashed lexical vectors supply a small ranking tie-breaker; these are not trained semantic embeddings. Comparison retrieval interleaves both versions. A per-request byte budget selects exact source excerpts while reserving room for instructions and output.

For local Ollama, the app uses `/api/chat` with an explicit context size and a JSON schema restricting citation references to the evidence actually sent. It validates responses, retries a malformed answer once, and reports model/validation errors separately from empty retrieval. Retrieved sources remain inspectable on error. The document viewer highlights the exact passage sent to the model. Citation validation checks reference membership, not independent factual entailment.

Defaults (environment variables override `.streamlit/secrets.toml`):

```toml
LLM_CONTEXT_TOKENS = "8192"
LLM_MAX_OUTPUT_TOKENS = "600"
LOCAL_LLM_API = "auto"
```

`auto` selects native Ollama for localhost port 11434. Use `ollama` explicitly for another Ollama endpoint, or `compatible` for a server implementing `/v1/chat/completions` and JSON-schema output. For compatible servers, configure their actual context window separately to match `LLM_CONTEXT_TOKENS`.

The answer's **Request diagnostics** section records pipeline version, retrieval/context counts, prompt bytes, attempts, elapsed time, and failure stage without storing raw model responses. Generate the same question again after a KB update to use the new revision, and pin a prior answer for comparison. Source viewers retain the document text at answer time. After backend edits, restart Streamlit so its imported Python modules are refreshed.

Run tests with:

```powershell
python -m pytest -q
```

## Notes

This is a starter implementation that matches the architecture intent from the design document, while keeping the demo fully local and dependency-light for quick iteration.
