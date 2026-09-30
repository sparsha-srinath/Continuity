"""Presentation workspace for changing evidence and observing real RAG behavior."""

import html
import json
from base64 import b64encode
from collections import Counter
from hashlib import sha256
from dataclasses import asdict, replace
from pathlib import Path

import streamlit as st
import pandas as pd

from .llm_provider import ProviderError, load_provider_config
from .codebase_import import prepare_codebase
from .models import SourceChunk
from .retrieval import split_chunks
from .workspace import AMI_QUESTION, AMI_UPDATE, LiveWorkspace


PAGES = ["Overview", "Knowledge base", "Chunk explorer", "Live Q&A"]
COLORS = ["#d6eac0", "#e5dff4", "#f5e6b8", "#cce8e3", "#f0d8c8", "#d8e3f4"]
TYPE_LABELS = {"doc": "▤ Document", "email": "✉ Email", "code": "⌘ Code",
               "ticket": "◈ Ticket", "runbook": "☷ Runbook", "spreadsheet": "▦ Spreadsheet"}
TYPE_COLORS = {"doc": "#e2ebfa", "email": "#ece2f6", "code": "#dceedd",
               "ticket": "#f8ebc9", "runbook": "#daeeeb", "spreadsheet": "#f4e0d3"}


def esc(value):
    return html.escape(str(value))


def markup(value):
    # HTML rendering keeps newlines / Markdown syntax in source passages literal.
    st.html(value)


def type_label(kind):
    return TYPE_LABELS.get(kind, kind.title())


def type_badge(kind):
    return f'<span class="type-badge" style="background:{TYPE_COLORS.get(kind, "#e8ece5")}">{esc(type_label(kind))}</span>'


def document_table(rows, **kwargs):
    frame = pd.DataFrame(rows)
    colors = {type_label(kind): color for kind, color in TYPE_COLORS.items()}
    styled = frame.style.map(lambda value: f"background-color: {colors.get(value, '#e8ece5')}; color: #29432f; font-weight: 600;", subset=["Type"])
    st.dataframe(styled, hide_index=True, use_container_width=True, **kwargs)


def go(page):
    st.session_state.page = page


def add_document():
    st.session_state.page = "Knowledge base"
    st.session_state.kb_tab = "Add document"


def draft_sample():
    st.session_state.draft_title = "AMI retry configuration — owner clarification"
    st.session_state.draft_text = AMI_UPDATE
    st.session_state.page = "Knowledge base"
    st.session_state.kb_tab = "Add document"


def ask_ami():
    st.session_state.question = AMI_QUESTION
    st.session_state.scope = "legacy"
    st.session_state.page = "Live Q&A"


def pin_answer(entry):
    st.session_state.before_answer = entry


def unpin_answer():
    st.session_state.pop("before_answer", None)


def heading(kicker, title, subtitle):
    markup(f'<div class="page-heading"><div class="eyebrow">{esc(kicker)}</div>'
           f'<h1>{esc(title)}</h1><p>{esc(subtitle)}</p></div>')


def stats(workspace):
    values = [(len(workspace.documents), "Source documents", "Documents currently in the KB"),
              (len(workspace.chunks), "Indexed chunks", f"{workspace.chunk_size:,} character limit"),
              (len({d.system_version for d in workspace.documents}), "System versions", "Versions represented in the KB"),
              (f"{workspace.revision:02}", "KB revision", "Current document and index revision")]
    markup('<div class="stats">' + ''.join(
        f'<div class="stat"><div class="label">{label}</div>'
        f'<strong>{value}</strong><small>{sub}</small></div>' for value, label, sub in values) + '</div>')


def activity(workspace, limit=5):
    markup(''.join(f'<div class="activity"><span class="time">{e["time"]}</span>'
                   f'<span class="action">{esc(e["action"])}</span>'
                   f'<span class="rev">REV {e["revision"]:02}</span></div>' for e in workspace.events[:limit]))


def action_feedback(workspace, key):
    slot = st.empty()
    receipt = st.session_state.get("action_receipt", {})
    if receipt.get("key") == key and receipt.get("revision") == workspace.revision:
        slot.success(receipt["message"])
    return slot


def mutate(workspace, operation, message, feedback_key, feedback_slot):
    try:
        with feedback_slot.container():
            with st.status("Updating the knowledge index…", expanded=True):
                operation()
        st.session_state.action_receipt = {"key": feedback_key, "message": message, "revision": workspace.revision}
        st.rerun()
    except (ValueError, RuntimeError) as error:
        feedback_slot.error(str(error))


def publish_source(workspace, title, text, system, source_type):
    receipt = st.session_state.get("publish_receipt", {})
    published = any(
        d.chunk_id == receipt.get("document_id")
        and (d.section_title, d.text, d.system_version, d.source_type)
        == (title.strip(), text, system, source_type)
        for d in workspace.documents
    )
    button_slot = st.empty()
    feedback_slot = st.empty()
    clicked = button_slot.button(
        "Published to knowledge base ✓" if published else "Publish to knowledge base",
        key="publish_source", type="primary", use_container_width=True,
        disabled=published or not title.strip() or not text.strip(),
    )
    if clicked and not published:
        button_slot.button("Publishing…", key="publish_source_busy", type="primary",
                           disabled=True, use_container_width=True)
        st.session_state.pop("publish_error", None)
        try:
            with feedback_slot.container():
                with st.status("Publishing your source…", expanded=True):
                    st.write("Adding the document and updating the search index. Please wait.")
                    document_id = workspace.upsert(title, text, system, source_type)
            st.session_state.publish_receipt = {"document_id": document_id, "revision": workspace.revision}
        except (ValueError, RuntimeError) as error:
            st.session_state.publish_error = f"Could not publish: {error} Your draft is still here. Try again."
        st.rerun()
    with feedback_slot.container():
        if st.session_state.get("publish_error"):
            st.error(st.session_state.publish_error)
        elif published:
            count = len(workspace.document_chunks(receipt["document_id"]))
            st.success(f"Published: {title.strip()} · Revision {receipt['revision']:02} · "
                       f"{count} indexed {'chunk' if count == 1 else 'chunks'}. Ready to use in Live Q&A.")
    return published


def sidebar(workspace):
    with st.sidebar:
        logo = b64encode(Path(__file__).with_name("continuity.svg").read_bytes()).decode("ascii")
        markup(f'<div class="wordmark"><img class="continuity-mark" src="data:image/svg+xml;base64,{logo}" '
               'alt="Continuity logo">continuity<span class="brand-period">.</span></div>'
               '<div class="side-label">Knowledge workspace</div>')
        st.radio("Workspace navigation", PAGES, key="page", label_visibility="collapsed")
        st.divider()
        markup('<div class="side-label">Demo steps</div>'
               '<div class="side-note">01 &nbsp; Generate a baseline answer<br>'
               '02 &nbsp; Publish the AMI clarification<br>03 &nbsp; Generate again and compare</div>')
        st.button("Load demo question", on_click=ask_ami, use_container_width=True)
        st.divider()
        try:
            config = load_provider_config()
            model = config.model or "No model configured"
            provider = "Local Ollama" if config.uses_ollama else config.provider.title()
            detail = "Configured model for answer generation" if config.provider != "none" else "Configure a model to generate answers"
        except ProviderError as error:
            model, provider, detail = "Configuration needs attention", "Provider", str(error)
        markup(f'<div class="side-model"><div class="side-label">{esc(provider)}</div>'
               f'<strong>{esc(model)}</strong><small>{esc(detail)}</small></div>')


def overview(workspace):
    markup('<div class="hero"><div class="eyebrow">Overview</div>'
           '<h1>Knowledge workspace</h1>'
           '<p>Manage source documents, inspect indexed passages, and generate answers '
           'using the configured model and knowledge base.</p>'
           '<div class="hero-foot"><span>Document management</span><span>Chunk inspection</span>'
           '<span>Questions and source citations</span></div>'
           '<div class="hero-art" aria-hidden="true"><div class="orbit"></div><div class="orbit inner"></div>'
           '<div class="art-document"><span></span><span></span><span></span><span></span><span></span><span></span></div>'
           '<div class="art-chip one">01 / source.md</div><div class="art-chip two">02 / chunks</div>'
           '<div class="art-chip three">03 / answer and citations</div></div></div>')
    stats(workspace)
    markup('<div class="section-heading"><h2>Workspace tools</h2></div>')
    cards = [("▤", "Knowledge base", "View, add, edit, or remove source documents. Publishing and saving rebuild the search index.", "Knowledge base", "Open knowledge base"),
             ("▦", "Chunk explorer", "Inspect passage boundaries, preview a different chunk size, and rebuild the index.", "Chunk explorer", "Open chunk explorer"),
             ("↗", "Questions and answers", "Ask a question, review cited sources, and compare answers from different KB revisions.", "Live Q&A", "Open Live Q&A")]
    for index, (column, card) in enumerate(zip(st.columns(3, gap="medium"), cards), 1):
        icon, title, description, page, action = card
        with column:
            markup(f'<div class="feature"><span class="feature-number">0{index}</span><span class="icon">{icon}</span>'
                   f'<h3>{title}</h3><p>{description}</p></div>')
            st.button(action, on_click=go, args=(page,), use_container_width=True)
    markup('<div class="flow"><div class="flow-node"><b>01 &nbsp; Add documents</b><small>Upload files or paste text</small></div>'
           '<span class="flow-arrow">→</span><div class="flow-node"><b>02 &nbsp; Split into chunks</b><small>Create searchable passages</small></div>'
           '<span class="flow-arrow">→</span><div class="flow-node"><b>03 &nbsp; Retrieve passages</b><small>Find matches for the question</small></div>'
           '<span class="flow-arrow">→</span><div class="flow-node"><b>04 &nbsp; Generate an answer</b><small>Use selected passages as context</small></div></div>')
    left, right = st.columns([1.25, 1], gap="large")
    with left:
        markup('<div class="section-heading"><h2>AMI retry settings demo</h2></div>')
        st.write("Ask for the exact AMI retry settings. Pin the first answer, add the owner’s clarification, "
                 "and ask the same question again to compare the answers and their sources.")
        st.button("Load AMI demo question", type="primary", on_click=ask_ami)
    with right:
        markup('<div class="section-heading"><h2>Recent KB changes</h2><span>Latest four changes</span></div>')
        activity(workspace, 4)


def preview_document(title, text, version="legacy"):
    return SourceChunk(chunk_id="PREVIEW", source_file=title, section_title=title, category="preview",
                       access="internal", source_type="doc", entity=title, author="Presenter",
                       author_role_at_time="Contributor", date="", employment_status="active",
                       confidence_score=0.75, text=text, system_version=version)


def strip(chunks):
    total = sum(len(c.text) for c in chunks) or 1
    markup('<div class="chunk-strip">' + ''.join(
        f'<span title="Chunk {i + 1}: {len(c.text)} characters" '
        f'style="flex:{len(c.text) / total};background:{COLORS[i % len(COLORS)]}">{i + 1}</span>'
        for i, c in enumerate(chunks)) + '</div>')


def chunk_cards(chunks, limit=None):
    offset = 0
    for index, chunk in enumerate(chunks[:limit] if limit else chunks):
        end = offset + len(chunk.text)
        markup(f'<div class="chunk-card" style="--chunk-color:{COLORS[index % len(COLORS)]}">'
               f'<b>Chunk {index + 1:02}</b><small>{len(chunk.text):,} chars · {offset:,}–{end:,}</small>'
               f'<p>{esc(chunk.text[:240])}{"…" if len(chunk.text) > 240 else ""}</p></div>')
        offset = end


def knowledge_base(workspace):
    heading("01 / Documents", "Knowledge base",
            "View and manage source documents. Publishing, saving, and removing documents update the search index.")
    stats(workspace)
    library, add, codebase, controls = st.tabs(["Document library", "Add document", "Import codebase", "Reset & activity"],
                                     key="kb_tab", on_change="rerun")
    with library:
        if not workspace.documents:
            st.info("The knowledge base is empty. Use Add document or restore the baseline in Reset & activity.")
        else:
            search, version_filter, type_filter = st.columns([2, 1, 1])
            term = search.text_input("Find a document", placeholder="Search titles or source paths…")
            version = version_filter.selectbox("Version filter", ["All versions", "Legacy", "Modernized"])
            kind_filter = type_filter.selectbox("Type filter", ["all", *TYPE_LABELS],
                                                format_func=lambda kind: "All types" if kind == "all" else type_label(kind))
            filtered = [d for d in workspace.documents if term.lower() in (d.section_title + d.source_file).lower()
                        and (kind_filter == "all" or d.source_type == kind_filter)
                        and (version == "All versions" or d.system_version == ("legacy" if version == "Legacy" else "mod_v1"))]
            if not filtered:
                st.info("No documents match these filters.")
            else:
                counts = Counter(c.chunk_id.split("::part-")[0] for c in workspace.chunks)
                st.caption(f"Showing {len(filtered)} of {len(workspace.documents)} documents currently in the KB. Select a source below the table to inspect or edit it.")
                document_table([
                    {"Document": d.section_title, "Version": "Legacy" if d.system_version == "legacy" else "Modernized",
                     "Type": type_label(d.source_type), "Chunks": counts[d.chunk_id], "Characters": len(d.text),
                     "Source path": d.source_file} for d in filtered
                ], height=min(360, 36 * (len(filtered) + 1)))
                names = {d.chunk_id: f"{type_label(d.source_type)} · {d.section_title} · {'Legacy' if d.system_version == 'legacy' else 'Modernized'}" for d in filtered}
                selected = st.selectbox("Source document", list(names), format_func=lambda key: names[key],
                                        key="source_document", index=None, placeholder="Choose a document to inspect or edit…")
                save_clicked = remove_clicked = False
                if selected is not None:
                    document = next(d for d in filtered if d.chunk_id == selected)
                    epoch = f"{workspace.revision}-{selected}"
                    markup(f'<div class="doc-summary"><div>{type_badge(document.source_type)}'
                           f'<small>{esc(document.source_file)}</small></div><span class="badge">Indexed</span></div>')
                    title = st.text_input("Document title", document.section_title, key=f"edit-title-{epoch}")
                    content = st.text_area("Source content", document.text, height=320, key=f"edit-text-{epoch}")
                    version_editor, type_editor = st.columns(2)
                    system = version_editor.selectbox("System version", ["legacy", "mod_v1"],
                                          index=0 if document.system_version == "legacy" else 1,
                                          format_func=lambda v: "Legacy" if v == "legacy" else "Modernized", key=f"edit-version-{epoch}")
                    kinds = list(dict.fromkeys([*TYPE_LABELS, document.source_type]))
                    kind = type_editor.selectbox("Document type", kinds, index=kinds.index(document.source_type),
                                                  format_func=type_label, key=f"edit-type-{epoch}")
                    with st.expander("Preview chunks", expanded=False):
                        st.caption("How this document’s current text will be split when saved. Use Chunk explorer for detailed inspection.")
                        parts = split_chunks([replace(document, text=content)], max_chars=workspace.chunk_size)
                        strip(parts)
                        st.caption(f"{len(parts)} chunks · {len(content):,} characters · {workspace.chunk_size:,} character limit")
                        chunk_cards(parts, 6)
                        if len(parts) > 6:
                            st.caption(f"Showing 6 of {len(parts)} chunks. Explore all chunks after saving.")
                    save, remove = st.columns([2, 1])
                    save_clicked = save.button("Save & reindex", type="primary", use_container_width=True)
                    remove_clicked = remove.button("Remove source", use_container_width=True)
                feedback = action_feedback(workspace, "document_editor")
                if save_clicked:
                    mutate(workspace, lambda: workspace.upsert(title, content, system, kind, selected),
                           "Document updated. The new content is now searchable.", "document_editor", feedback)
                if remove_clicked:
                    mutate(workspace, lambda: workspace.remove(selected), "Source and its chunks removed from the index.",
                           "document_editor", feedback)
    with add:
        edit, preview = st.columns([1.4, 1], gap="large")
        with edit:
            st.subheader("Add a document")
            st.caption("Paste text or upload UTF-8 text, Markdown, Python, SQL, CSV, or JSON. Maximum 500 KB.")
            upload = st.file_uploader("Upload a source", type=["txt", "md", "py", "sql", "csv", "json"], max_upload_size=1)
            if upload is not None and st.button("Use uploaded content"):
                try:
                    raw = upload.getvalue()
                    if len(raw) > 500_000:
                        raise ValueError("Keep each demo document below 500 KB.")
                    st.session_state.draft_text = raw.decode("utf-8-sig")
                    st.session_state.draft_title = Path(upload.name).name
                    st.rerun()
                except (UnicodeError, ValueError) as error:
                    st.error(f"Cannot read this source as UTF-8 text: {error}")
            title = st.text_input("New document title", key="draft_title", placeholder="e.g. AMI retry owner clarification")
            text = st.text_area("New source content", key="draft_text", height=300, placeholder="Paste the document text to index…")
            version, kind = st.columns(2)
            system = version.selectbox("New source version", ["legacy", "mod_v1"], format_func=lambda v: "Legacy" if v == "legacy" else "Modernized")
            source_type = kind.selectbox("Source type", list(TYPE_LABELS), format_func=type_label)
            published = publish_source(workspace, title, text, system, source_type)
            st.button("Load sample document", on_click=draft_sample)
        with preview:
            st.subheader("Chunk preview")
            if text.strip():
                parts = split_chunks([preview_document(title, text, system)], max_chars=workspace.chunk_size)
                strip(parts)
                st.caption(f"{len(parts)} {'chunk' if len(parts) == 1 else 'chunks'} · "
                           f"{'Published and searchable' if published else 'Preview only until published'}")
                chunk_cards(parts, 5)
            else:
                markup('<div class="empty-state"><b>No document text entered</b><p>Paste text or load a file to preview '
                       'its chunks. Publish the document to add it to the search index.</p></div>')
    with codebase:
        import_codebase_view(workspace)
    with controls:
        reset, log = st.columns([1, 1.3], gap="large")
        with reset:
            st.subheader("Reset knowledge base")
            st.write("Restore the original demo documents or remove all documents from the current knowledge base.")
            st.caption("These actions affect this session’s documents and search index. Original files remain intact. Earlier answers keep their revision labels.")
            restore_clicked = st.button("Restore baseline corpus", type="primary", use_container_width=True)
            clear_clicked = st.button("Clear knowledge base", use_container_width=True)
            feedback = action_feedback(workspace, "reset")
            if restore_clicked:
                mutate(workspace, workspace.reset, "Baseline documents and default chunk size restored.", "reset", feedback)
            if clear_clicked:
                mutate(workspace, lambda: workspace.reset(empty=True), "Knowledge base cleared. No documents are indexed.", "reset", feedback)
            st.download_button("Export workspace documents", json.dumps([asdict(d) for d in workspace.documents], indent=2),
                               file_name=f"continuity-revision-{workspace.revision}.json", mime="application/json", use_container_width=True)
        with log:
            st.subheader("Revision history")
            activity(workspace, 15)


def import_codebase_view(workspace):
    st.subheader("Import source files")
    st.write("Upload a ZIP of your repository to preserve its folder structure, or select several source files together.")
    st.caption("20 MB combined upload · Up to 500 text files / 10 MB expanded per batch · 500 KB per source. "
               "Dependencies, build output, binary files, and common credential filenames are skipped. Review the preview before publishing.")
    uploads = st.file_uploader("Codebase ZIP or source files", accept_multiple_files=True, max_upload_size=20,
                               key="codebase_uploads")
    left, right = st.columns([2, 1])
    project = left.text_input("Codebase name", placeholder="e.g. billing-service", key="import_project")
    version = right.selectbox("Codebase version", ["legacy", "mod_v1"],
                              format_func=lambda v: "Legacy" if v == "legacy" else "Modernized")
    payloads = [(upload.name, upload.getvalue()) for upload in uploads]
    signature = tuple((name, sha256(data).hexdigest()) for name, data in payloads)
    if st.button("Preview codebase import", disabled=not uploads, type="primary"):
        st.session_state.pop("import_plan", None)
        try:
            with st.spinner("Reading source files…"):
                st.session_state.import_plan = prepare_codebase(payloads)
                st.session_state.import_signature = signature
        except ValueError as error:
            st.error(str(error))
    plan = st.session_state.get("import_plan")
    if plan is None:
        return
    if signature != st.session_state.get("import_signature"):
        st.info("The upload changed. Preview it again before importing.")
        return
    st.caption(f"{len(plan.files)} source files ready · {len(plan.skipped)} files skipped")
    if plan.skipped:
        with st.expander(f"Skipped files ({len(plan.skipped)})"):
            st.dataframe(plan.skipped, hide_index=True, use_container_width=True)
    if not plan.files:
        st.info("No supported source files found. Upload UTF-8 source code or documentation.")
        return
    excluded = st.multiselect("Exclude additional files", [source.path for source in plan.files],
                              key=f"import-excludes-{sha256(repr(signature).encode()).hexdigest()[:16]}")
    selected = [source for source in plan.files if source.path not in excluded]
    if selected:
        document_table([{"Path": source.path, "Type": type_label(source.source_type), "Characters": len(source.text)}
                        for source in selected], height=300)
    else:
        st.info("All files are excluded. Select at least one source to import.")
    inspect = st.selectbox("Preview source text", [source.path for source in plan.files])
    with st.expander("Selected file contents"):
        st.code(next(source.text for source in plan.files if source.path == inspect), language="text", wrap_lines=True)
    st.caption("One publish updates the whole batch. Reimporting the same codebase name, version, and path updates that source; "
               "other sources already in the KB are kept. Files are indexed as text and are never executed.")
    import_clicked = st.button(f"Import {len(selected)} files & index", type="primary", disabled=not selected or not project.strip())
    feedback = action_feedback(workspace, "codebase_import")
    if import_clicked:
        mutate(workspace, lambda: workspace.import_codebase(selected, project, version),
               f"Imported {len(selected)} files from {project.strip()}. Open Document library or Chunk explorer to inspect them.",
               "codebase_import", feedback)


def chunk_explorer(workspace):
    heading("02 / Index inspection", "Chunk explorer",
            "Inspect how a selected document is split into passages. Preview a chunk size change, then apply it to all documents.")
    if not workspace.documents:
        st.info("The index is empty. Add a source in Knowledge base to visualize its chunks.")
        st.button("Open knowledge base", on_click=go, args=("Knowledge base",))
        return
    source, size = st.columns([1.8, 1], gap="large")
    counts = Counter(c.chunk_id.split("::part-")[0] for c in workspace.chunks)
    names = {d.chunk_id: f"{type_label(d.source_type)} · {d.section_title} · {len(d.text):,} chars · {counts[d.chunk_id]} indexed chunks"
             for d in workspace.documents}
    default = max(range(len(workspace.documents)), key=lambda i: len(workspace.documents[i].text))
    selected = source.selectbox("Document to inspect", list(names), index=default, format_func=lambda key: names[key])
    document = next(d for d in workspace.documents if d.chunk_id == selected)
    chunk_size = size.slider("Maximum characters per chunk", 200, 3000, workspace.chunk_size, 100,
                             key=f"chunk-size-{workspace.revision}")
    parts = workspace.document_chunks(selected, chunk_size)
    changed = chunk_size != workspace.chunk_size
    a, b, c = st.columns([1, 1, 1.3])
    a.metric("Document length", f"{len(document.text):,}", help="Characters in the source document")
    b.metric("Preview chunks" if changed else "Indexed chunks", len(parts))
    c.metric("Boundary strategy", "Paragraph → line", help="No overlap. Split at paragraph or line boundaries when possible, then the character limit.")
    preview_notice = st.empty()
    single_chunk_notice = st.empty()
    if changed:
        preview_notice.info(f"Previewing {chunk_size:,} characters. The live index still uses {workspace.chunk_size:,} until you rebuild.")
    if len(parts) == 1:
        single_chunk_notice.info(f"One chunk is expected: this document has {len(document.text):,} characters and the selected limit is "
                f"{chunk_size:,}. This view shows one document, not the entire KB. "
                "Choose a longer document or reduce the slider to preview more chunks.")
    rebuild_clicked = st.button("Apply chunk size & rebuild index", type="primary", disabled=not changed)
    feedback = action_feedback(workspace, "chunk_rebuild")
    if rebuild_clicked:
        mutate(workspace, lambda: workspace.rebuild(chunk_size), "Index rebuilt with the new chunk boundaries.",
               "chunk_rebuild", feedback)
    strip(parts)
    st.caption("Matching colors connect the source text to its chunks. Boundaries use characters, not model tokens; passages have no overlap.")
    left, right = st.columns([1.35, 1], gap="large")
    with left:
        st.subheader("Source text")
        markup(type_badge(document.source_type))
        markup(f'<div class="mono" style="margin-bottom:10px">{esc(document.source_file)}</div>')
        markup('<div class="source-canvas">' + ''.join(
            f'<mark title="Chunk {i + 1}" style="background:{COLORS[i % len(COLORS)]}">{esc(part.text)}</mark>'
            for i, part in enumerate(parts)) + '</div>')
    with right:
        st.subheader("Document chunks")
        st.caption(f"{len(parts)} exact passages · Each keeps its source and system version")
        with st.container(height=620, border=False):
            chunk_cards(parts)
        choice = st.selectbox("Inspect a full chunk", range(len(parts)), format_func=lambda i: f"Chunk {i + 1:02}")
        with st.expander("Full chunk text & metadata"):
            st.code(parts[choice].text, language="text", wrap_lines=True)
            st.json({"chunk_id": parts[choice].chunk_id, "system_version": document.system_version,
                     "source_type": document.source_type, "characters": len(parts[choice].text)})


def parameter_help(label, explanation):
    return (f'<details class="parameter-help" name="retrieval-help">'
            f'<summary aria-label="About {esc(label)}" title="About {esc(label)}">?</summary>'
            f'<div class="parameter-definition"><strong>{esc(label)}</strong><p>{esc(explanation)}</p></div></details>')


def trace(result):
    diagnostic = result.get("diagnostics", {})
    candidates = result.get("retrieved_evidence", []) or result.get("evidence", [])
    maximum = max((c.get("score") or 0 for c in candidates), default=1) or 1
    rows = []
    for i, candidate in enumerate(candidates):
        score = candidate.get("score") or 0
        rows.append(
            f'<div class="trace-row"><span class="trace-rank">{i + 1:02}</span>'
            f'<div class="trace-body"><b>{esc(candidate.get("section_title", "Source"))}</b>'
            f'<div class="trace-bar" aria-hidden="true"><i style="width:{max(0, min(100, score / maximum * 100)):.1f}%"></i></div></div>'
            f'<span class="trace-score">{score:.2f}</span>'
            + parameter_help(f"Relevance score for passage {i + 1}",
                             "How closely this passage matches your question. Higher scores mean a stronger search match. "
                             "This is not a percentage or a measure of answer accuracy. The bar compares it with the highest score in this list.")
            + '</div>'
        )
    elapsed = diagnostic.get("elapsed_seconds")
    stage = diagnostic.get("stage", "retrieval")
    stage_definition = {
        "configuration": "The request reached the model setup check. Review any configuration error shown with the answer.",
        "retrieval": "The request reached the source search step. If no matching passages are found, answer generation does not start.",
        "context": "The request reached input preparation, where source passages are fitted into the model's input limit.",
        "generation": "The request reached the model call. If it failed, review the error shown with the answer.",
        "validation": "The request reached the checks for response format and valid source references.",
        "complete": "The model returned an answer and the response format and citation checks finished. This does not guarantee that every claim is correct.",
    }.get(stage, "The last processing step recorded for this request.")
    metrics = [
        ("Retrieved passages", diagnostic.get("retrieved_chunks", "—"),
         "The number of matching passages selected by the search step, before fitting them into the model's input limit."),
        ("Sent to model", diagnostic.get("context_chunks", "—"),
         "The number of passages included with your question for the model to read. This can be lower than Retrieved passages if the input is too large."),
        ("Prompt size", f"{diagnostic['prompt_bytes']:,} bytes" if "prompt_bytes" in diagnostic else "—",
         "The size of the initial instructions, question, and source text, measured in UTF-8 bytes. Bytes measure data size; they are not words or model tokens."),
        ("Generation attempts", diagnostic.get("attempts", "—"),
         "How many times the app tried to generate this answer. Usually 1; it can retry once if the first response fails its format or citation checks."),
        ("Stage", str(stage).replace("_", " ").capitalize(), stage_definition),
        ("Elapsed time", f"{elapsed:.1f}s" if elapsed is not None else "—",
         "Time spent preparing the model input, generating the answer, and checking it, including any retry. This timer starts after the source search. A dash means the value was not recorded."),
    ]
    with st.container(key="retrieval_details", border=True):
        markup('<div class="retrieval-heading"><h3>Retrieval details</h3>'
               '<p>Source matches and processing details for this answer.</p></div>')
        markup('<div class="retrieval-list-heading"><span>Source passages</span>'
               + parameter_help("Passage order", "The position of each passage in the selected source list. In Compare both systems mode, legacy and modernized passages alternate so both systems are represented.")
               + '</div>' + (''.join(rows) or '<p class="retrieval-empty">No relevant passages retrieved.</p>'))
        markup('<dl class="retrieval-metrics">' + ''.join(
            f'<div class="retrieval-metric"><dt>{esc(label)}</dt><dd>{esc(value)}</dd>'
            + parameter_help(label, explanation + (" This value was not recorded for this request." if value == "—" else ""))
            + '</div>' for label, value, explanation in metrics
        ) + '</dl>')
        with st.expander("Technical request data"):
            st.caption("The recorded values for this request. Missing values were not recorded.")
            st.json(diagnostic)


def show_sources(entry):
    result = entry["result"]
    sources = result.get("evidence", []) or result.get("retrieved_evidence", [])
    st.markdown("##### Cited evidence" if result.get("evidence") else "##### Retrieved sources")
    for index, source in enumerate(sources):
        with st.expander(f"{index + 1:02} · {type_label(source.get('source_type', 'doc'))} · {source.get('section_title', 'Source')} · {'Modernized' if source.get('system_version') == 'mod_v1' else 'Legacy'}"):
            markup(type_badge(source.get("source_type", "doc")))
            st.caption(source.get("source", "Indexed record"))
            passage = source.get("details") or source.get("text", "")
            st.code(passage, language="text", wrap_lines=True)
            snapshot = entry.get("documents", {}).get(source["chunk_id"])
            if snapshot:
                full_text = snapshot["text"]
                start = full_text.find(passage)
                if start >= 0 and passage:
                    rendered = esc(full_text[:start]) + f'<mark style="background:#d6eac0">{esc(passage)}</mark>' + esc(full_text[start + len(passage):])
                else:
                    rendered = esc(full_text)
                st.markdown("**Full source at answer time**")
                markup(f'<div class="source-canvas">{rendered}</div>')
            st.download_button("Download cited passage", passage, file_name=f"{source['chunk_id']}.txt",
                               key=f"download-{entry['id']}-{index}")


def answer_body(entry):
    result = entry["result"]
    if result["status"] == "error":
        st.error(result["summary"])
    elif result["status"] in {"gap", "unsupported"}:
        st.warning(result["summary"])
    else:
        st.markdown(result["summary"])
    scope_label = {"legacy": "Legacy", "mod_v1": "Modernized", "compare": "Both systems"}[entry["scope"]]
    st.caption(f"KB revision {entry['revision']:02} · {scope_label} · {len(result.get('evidence', []))} cited passages")


def live_qa(workspace):
    heading("03 / Questions and answers", "Live Q&A",
            "Generate answers from the indexed documents. Review source citations or pin an answer to compare it after a KB update.")
    st.session_state.setdefault("question", st.session_state.get("last_question", AMI_QUESTION))
    st.session_state.setdefault("scope", st.session_state.get("last_scope", "legacy"))
    st.session_state.setdefault("answers", [])
    with st.form("ask-form"):
        question = st.text_area("Your question", key="question", height=85)
        scope_col, action = st.columns([1, 2], vertical_alignment="bottom")
        scope = scope_col.selectbox("Source scope", ["legacy", "mod_v1", "compare"], key="scope",
                                    format_func=lambda v: {"legacy": "Legacy only", "mod_v1": "Modernized only", "compare": "Compare both systems"}[v])
        submitted = action.form_submit_button("Generate answer", type="primary", use_container_width=True)
    # Keep progress and results at fixed positions on every rerun. Clearing the
    # results before a slow model call prevents the prior answer lingering as a
    # stale, duplicated panel while the new one is being rendered.
    progress_slot = st.empty()
    results_slot = st.empty()
    if submitted and question.strip():
        st.session_state.last_question = question
        st.session_state.last_scope = scope
        results_slot.empty()
        with progress_slot.container():
            with st.status("Retrieving evidence and calling the model…", expanded=True) as status:
                st.write(f"Using KB revision {workspace.revision:02} · {len(workspace.chunks)} indexed chunks")
                result = workspace.assistant().answer_question(question, scope)
                status.update(label="Answer ready" if result["status"] != "error" else "Answer generation needs attention",
                              state="complete" if result["status"] != "error" else "error", expanded=False)
        snapshots = {}
        for source in result.get("evidence", []) + result.get("retrieved_evidence", []):
            base_id = source["chunk_id"].split("::part-")[0]
            document = next((d for d in workspace.documents if d.chunk_id == base_id), None)
            if document:
                snapshots[source["chunk_id"]] = {"text": document.text, "title": document.section_title}
        entry = {"id": len(st.session_state.answers), "question": question, "scope": scope,
                 "revision": workspace.revision, "result": result, "documents": snapshots}
        st.session_state.answers.append(entry)
        st.session_state.answer_history = entry["id"]
    with results_slot.container(key="qa_results"):
        render_answer_results(workspace)


def render_answer_results(workspace):
    if not st.session_state.answers:
        markup('<div class="empty-state"><b>No answers generated</b><p>Enter a question and choose a source scope, then select Generate answer.</p></div>')
        st.button("Add document", on_click=add_document)
        return
    answers = st.session_state.answers
    index = st.selectbox("Answer history", range(len(answers) - 1, -1, -1),
                         key="answer_history",
                         format_func=lambda i: f"#{i + 1} · Rev {answers[i]['revision']:02} · {answers[i]['question'][:90]}")
    entry = answers[index]
    revision_notice = st.empty()
    if entry["revision"] != workspace.revision:
        revision_notice.info(f"This answer used revision {entry['revision']:02}. The current KB is revision {workspace.revision:02}. Generate again to use current evidence.")
    main, detail = st.columns([1.8, 1], gap="large")
    with main:
        st.subheader("Generated answer")
        answer_body(entry)
        pin, update = st.columns(2)
        pin.button("Pin baseline", on_click=pin_answer, args=(entry,), use_container_width=True)
        update.button("Add document", on_click=add_document, use_container_width=True)
        before = st.session_state.get("before_answer")
        with st.container(key="qa_comparison"):
            if before:
                with st.expander("Before & after", expanded=True):
                    if before["id"] == entry["id"]:
                        st.info("Baseline pinned. Update the KB, then generate the same question again to compare.")
                    else:
                        if before["question"] != entry["question"] or before["scope"] != entry["scope"]:
                            st.warning("These answers use different questions or scopes. Use the same inputs for a meaningful comparison.")
                        first, second = st.columns(2)
                        with first:
                            st.markdown(f"**Before · revision {before['revision']:02}**")
                            answer_body(before)
                        with second:
                            st.markdown(f"**After · revision {entry['revision']:02}**")
                            answer_body(entry)
                    st.button("Unpin comparison", on_click=unpin_answer)
        with st.container(key="qa_sources"):
            show_sources(entry)
    with detail:
        trace(entry["result"])


def run():
    st.set_page_config(page_title="Continuity · Knowledge workspace",
                       page_icon=str(Path(__file__).with_name("continuity.svg")),
                       layout="wide", initial_sidebar_state="expanded")
    markup('<style>' + Path(__file__).with_name("ui.css").read_text(encoding="utf-8") + '</style>')
    startup_slot = st.empty()
    if "workspace" not in st.session_state:
        with startup_slot.container():
            with st.spinner("Loading documents and building the search index…"):
                st.session_state.workspace = LiveWorkspace()
        startup_slot.empty()
    workspace = st.session_state.workspace
    sidebar(workspace)
    page = st.session_state.page
    st.session_state.mobile_page = page
    with st.container(key="mobile_navigation"):
        st.selectbox("Navigate workspace", PAGES, key="mobile_page",
                     on_change=lambda: go(st.session_state.mobile_page))
    markup(f'<div class="topline"><span>Workspace &nbsp;/&nbsp; <strong>{esc(page)}</strong></span>'
           f'<span class="badge"><i class="dot"></i> KB REVISION {workspace.revision:02}</span></div>')
    page_slot = st.empty()
    with page_slot.container(key=f"page_{PAGES.index(page)}"):
        {"Overview": overview, "Knowledge base": knowledge_base, "Chunk explorer": chunk_explorer, "Live Q&A": live_qa}[page](workspace)
