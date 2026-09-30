# A live demo with a before and after

Run `./run_demo.ps1 -Install` the first time, then `./run_demo.ps1` for later
sessions. Open http://127.0.0.1:8502. Use `-Port 8503` if needed. Python 3.11+
is required. Other platforms can use `python -m streamlit run app.py` after
installing requirements. Start your configured model before presenting.
The sidebar names the configured provider/model; it is not a health check.

## Five-minute presentation

1. **Overview:** introduce the real pipeline: source documents, chunking,
   retrieval, and grounded generation. Counts reflect the current index.
2. **Start live demo:** generate a live answer to the exact retry
   limits/timings question in Legacy scope. Open the cited evidence. The
   baseline has only a general backoff description and an old email about
   missing documentation. Click **Pin as before**.
3. **Add new evidence:** click **Add new evidence +**. The Add evidence tab
   opens with a synthetic owner clarification in an editable draft. Read or
   edit the values, watch the chunk preview, then click **Publish to knowledge
   base**. The KB revision and document/chunk counts update immediately.
4. **Chunk explorer:** select the new source. Adjust the character limit to
   preview boundaries. **Apply chunk size & rebuild index** makes the preview
   the actual index for all documents. The colored source text and chunk cards
   show the same exact passages, with no overlap.
5. **Live Q&A:** generate the same question again. Open **Before & after**,
   inspect the new citation, and show the retrieval scores and request details.
   The newly supplied values are 4 retries with 5/10/20/40-second delays; this
   is sample evidence, not a prepared answer. Model responses can vary.
6. **Knowledge base → Reset & activity:** restore the baseline for another
   presentation. Or clear the KB to show that no evidence yields no answer,
   then add a source from scratch. Old answers remain labeled with their KB
   revision and keep source snapshots from the time they were generated.

## Additional live interactions

- **Document library** shows a searchable inventory of all KB documents,
  including version, source type, chunk count, character count, and source path.
  Use the source selector below the table to inspect or edit a document.
  Colored type tags distinguish Email, Code, Document, Ticket, Runbook, and
  Spreadsheet sources. Filter by type or change **Document type** in the editor
  and use **Save & reindex** to update the tag throughout the workspace.
- **Import codebase** accepts a repository ZIP or multiple source files.
  Set a codebase name and version, click **Preview codebase import**, review
  included/skipped paths, optionally exclude files, then **Import files & index**.
  ZIP uploads preserve folder structure. Reimporting the same name/version/path
  updates that document; sources not present in a later upload are retained.
  The importer reads text; it does not execute code or build the project.
  Limits per batch: 20 MB uploaded, 10 MB expanded source, 500 supported files,
  and 500 KB per file. Split larger repositories. Dependencies, build output,
  binary files, and common credential filenames are skipped with reasons.
  To package committed files from a Git repository, use
  `git archive --format=zip --output=codebase.zip HEAD` in that repository.
  This command excludes uncommitted changes.
- Filter the document library by title/path and system version.
- Edit a source and click **Save & reindex**, or remove it and its chunks.
- Upload UTF-8 .txt, .md, .py, .sql, .csv, or .json content (500 KB maximum),
  click **Use uploaded content**, review the draft, then publish.
- Compare both system versions for BLPTS renewal fees or inspection rationale.
- Change a sample value, regenerate the same question, and inspect the changed
  evidence rather than relying on predetermined wording.
- Download cited passages or export the current documents as a JSON snapshot.

## What is real, and what is isolated

All answers use the existing live model pipeline, including context budgeting,
JSON validation, citation validation, and explicit failures. Retrieval uses BM25
with a small hashed lexical vector tie-breaker in a real Chroma collection.
The displayed scores are relevance scores, not confidence probabilities.
Chunk size is measured in characters, not model tokens.

The corpus and provided owner-clarification draft are synthetic. There are no
scripted answers. A missing/stopped model produces an explicit error with
retrieved sources still available; editing, reset, and chunk exploration do not
require a model. Citation validation checks membership, not factual entailment.

Each browser session has its own documents and Chroma collection. Changes do
not alter repository files or the normal persistent index. A refresh/new browser
session or server restart can start a fresh baseline; use the export action if
you want a copy of your documents. The JSON export is an archival snapshot,
not an automatic workspace import format. Use the same browser tab throughout
one demonstration to retain pinned answers and uploaded sources.
