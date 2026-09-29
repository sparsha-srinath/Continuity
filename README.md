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

On the `demo` branch, launch the guided presentation with:

```powershell
./run_demo.ps1 -Install # First run; installs dependencies
./run_demo.ps1          # Subsequent runs
```

The demo opens on port 8502 and needs no model or API key after dependency
setup. Four prepared scenarios cover the BLPTS renewal fee fix, inspection
rationale, surcharge documentation drift, and the AMI knowledge gap. Each
includes local source links and presenter notes. **Ask live model** runs the
same question through the existing model pipeline when a provider is configured.
Prepared content is explicitly labeled and separate from live answers.

See [the five-minute presenter guide](docs/presenter-demo.md). You can also
enable **Guided demo** in the regular app or open `/?demo=1`.

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

The answer's **Answer details** section records pipeline version, retrieval/context counts, prompt bytes, attempts, elapsed time, and failure stage without storing raw model responses. Old conversation entries have a **Regenerate answer** action. After backend edits, restart Streamlit so its imported Python modules are refreshed.

Run tests with:

```powershell
python -m pytest -q
```

## Notes

This is a starter implementation that matches the architecture intent from the design document, while keeping the demo fully local and dependency-light for quick iteration.
