"""Presentation workspace for changing evidence and observing real RAG behavior."""

import html
import json
from dataclasses import asdict, replace
from pathlib import Path

import streamlit as st

from .llm_provider import ProviderError, load_provider_config
from .models import SourceChunk
from .retrieval import split_chunks
from .workspace import AMI_QUESTION, AMI_UPDATE, LiveWorkspace


PAGES = ["Overview", "Knowledge base", "Chunk explorer", "Live Q&A"]
COLORS = ["#d6eac0", "#e5dff4", "#f5e6b8", "#cce8e3", "#f0d8c8", "#d8e3f4"]


def esc(value):
    return html.escape(str(value))


def markup(value):
    # HTML rendering keeps newlines / Markdown syntax in source passages literal.
    st.html(value)


def go(page):
    st.session_state.page = page


def draft_sample():
    st.session_state.draft_title = "AMI retry configuration — owner clarification"
    st.session_state.draft_text = AMI_UPDATE
    st.session_state.page = "Knowledge base"
    st.session_state.kb_tab = "Add evidence"


def ask_ami():
    st.session_state.question = AMI_QUESTION
    st.session_state.scope = "legacy"
    st.session_state.page = "Live Q&A"


def heading(kicker, title, subtitle):
    markup(f'<div class="page-heading"><div class="eyebrow">{esc(kicker)}</div>'
           f'<h1>{esc(title)}</h1><p>{esc(subtitle)}</p></div>')


def stats(workspace):
    values = [(len(workspace.documents), "Source documents", "In this live workspace"),
              (len(workspace.chunks), "Indexed chunks", f"{workspace.chunk_size:,} character limit"),
              (len({d.system_version for d in workspace.documents}), "System versions", "Legacy & modernized"),
              (f"{workspace.revision:02}", "KB revision", "Every change is traceable")]
    markup('<div class="stats">' + ''.join(
        f'<div class="stat"><div class="label">{label}<span>↗</span></div>'
        f'<strong>{value}</strong><small>{sub}</small></div>' for value, label, sub in values) + '</div>')


def activity(workspace, limit=5):
    markup(''.join(f'<div class="activity"><span class="time">{e["time"]}</span>'
                   f'<span class="action">{esc(e["action"])}</span>'
                   f'<span class="rev">REV {e["revision"]:02}</span></div>' for e in workspace.events[:limit]))


def mutate(workspace, operation, message):
    try:
        with st.spinner("Updating the knowledge index…"):
            operation()
        st.session_state.flash = message
        st.rerun()
    except (ValueError, RuntimeError) as error:
        st.error(str(error))


def sidebar(workspace):
    with st.sidebar:
        markup('<div class="wordmark"><b>c</b>continuity<span style="color:#afd995">.</span></div>'
               '<div class="side-label">Modernization studio</div>')
        st.radio("Workspace navigation", PAGES, key="page", label_visibility="collapsed")
        st.divider()
        markup('<div class="side-label">Live demo workflow</div>'
               '<div class="side-note">01 &nbsp; Ask with the current evidence<br>'
               '02 &nbsp; Add what was missing<br>03 &nbsp; Watch the answer change</div>')
        st.button("Start the AMI workflow ↗", on_click=ask_ami, use_container_width=True)
        st.button("Load a sample update +", on_click=draft_sample, use_container_width=True)
        st.divider()
        try:
            config = load_provider_config()
            model = config.model or "No model configured"
            provider = "Local Ollama" if config.uses_ollama else config.provider.title()
            detail = "Configured · answers generated live" if config.provider != "none" else "Set a provider to generate answers"
        except ProviderError as error:
            model, provider, detail = "Configuration needs attention", "Provider", str(error)
        markup(f'<div class="side-model"><div class="side-label">{esc(provider)}</div>'
               f'<strong>{esc(model)}</strong><small>{esc(detail)}</small></div>'
               '<div class="side-note" style="margin-top:16px">Session workspace · Synthetic corpus<br>'
               'Edits stay in this browser session. Restore the baseline whenever you need a fresh start.</div>')


def overview(workspace):
    markup('<div class="hero"><div class="eyebrow">The live modernization workspace</div>'
           '<h1>Make change.<br><em>Keep the context.</em></h1>'
           '<p>Bring your legacy knowledge forward. Update the evidence, see how it is understood, '
           'and follow every answer back to its source.</p>'
           '<div class="hero-foot"><span>◉ &nbsp;Live knowledge base</span><span>◇ &nbsp;Visible retrieval</span>'
           '<span>↗ &nbsp;Source-backed answers</span></div>'
           '<div class="hero-art" aria-hidden="true"><div class="orbit"></div><div class="orbit inner"></div>'
           '<div class="art-document"><span></span><span></span><span></span><span></span><span></span><span></span></div>'
           '<div class="art-chip one">01 / source.md</div><div class="art-chip two">02 / chunks</div>'
           '<div class="art-chip three">03 / grounded answer ↗</div></div></div>')
    stats(workspace)
    markup('<div class="section-heading"><h2>From source to understanding</h2><span>A real pipeline. Open at every step.</span></div>')
    cards = [("▤", "Your knowledge, alive.", "Add, edit, and remove source documents. Changes reach the search index immediately.", "Knowledge base", "Open knowledge base →"),
             ("▦", "See the pieces connect.", "Explore document boundaries, tune chunk size, and watch the index take shape.", "Chunk explorer", "Explore chunks →"),
             ("↗", "Ask. Inspect. Compare.", "Generate an answer with your model. Inspect retrieval and compare before and after.", "Live Q&A", "Ask a question →")]
    for index, (column, card) in enumerate(zip(st.columns(3, gap="medium"), cards), 1):
        icon, title, description, page, action = card
        with column:
            markup(f'<div class="feature"><span class="feature-number">0{index}</span><span class="icon">{icon}</span>'
                   f'<h3>{title}</h3><p>{description}</p></div>')
            st.button(action, on_click=go, args=(page,), use_container_width=True)
    markup('<div class="flow"><div class="flow-node"><b>01 &nbsp; Ingest</b><small>Files & knowledge updates</small></div>'
           '<span class="flow-arrow">→</span><div class="flow-node"><b>02 &nbsp; Chunk</b><small>Exact source passages</small></div>'
           '<span class="flow-arrow">→</span><div class="flow-node"><b>03 &nbsp; Retrieve</b><small>Rank relevant evidence</small></div>'
           '<span class="flow-arrow">→</span><div class="flow-node"><b>04 &nbsp; Answer</b><small>Live model & citations</small></div></div>')
    left, right = st.columns([1.25, 1], gap="large")
    with left:
        markup('<div class="section-heading"><h2>A demo with a before & after</h2><span>Try the AMI workflow</span></div>')
        st.write("Ask for the exact AMI retry settings. Pin the first answer, add the owner’s clarification, "
                 "and ask again. See new evidence become a new answer.")
        st.button("Start live workflow →", type="primary", on_click=ask_ami)
    with right:
        markup('<div class="section-heading"><h2>Workspace activity</h2><span>Changes as they happen</span></div>')
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
    heading("01 / Evidence management", "A knowledge base that moves with you.",
            "Publish new evidence, correct a source, or start fresh. Every update rebuilds the live index.")
    stats(workspace)
    library, add, controls = st.tabs(["Document library", "Add evidence", "Reset & activity"],
                                     key="kb_tab", on_change="rerun")
    with library:
        if not workspace.documents:
            st.info("Your knowledge base is empty. Add evidence or restore the baseline in Reset & activity.")
        else:
            search, version_filter = st.columns([3, 1])
            term = search.text_input("Find a document", placeholder="Search titles or source paths…")
            version = version_filter.selectbox("Version filter", ["All versions", "Legacy", "Modernized"])
            filtered = [d for d in workspace.documents if term.lower() in (d.section_title + d.source_file).lower()
                        and (version == "All versions" or d.system_version == ("legacy" if version == "Legacy" else "mod_v1"))]
            if not filtered:
                st.info("No documents match these filters.")
            else:
                editor, preview = st.columns([1.45, 1], gap="large")
                with editor:
                    names = {d.chunk_id: f"{d.section_title} · {'Legacy' if d.system_version == 'legacy' else 'Modernized'}" for d in filtered}
                    selected = st.selectbox("Source document", list(names), format_func=lambda key: names[key])
                    document = next(d for d in filtered if d.chunk_id == selected)
                    epoch = f"{workspace.revision}-{selected}"
                    markup(f'<div class="doc-summary"><div><b>{esc(document.source_type.title())} source</b>'
                           f'<small>{esc(document.source_file)}</small></div><span class="badge">Indexed</span></div>')
                    title = st.text_input("Document title", document.section_title, key=f"edit-title-{epoch}")
                    content = st.text_area("Source content", document.text, height=320, key=f"edit-text-{epoch}")
                    system = st.selectbox("System version", ["legacy", "mod_v1"],
                                          index=0 if document.system_version == "legacy" else 1,
                                          format_func=lambda v: "Legacy" if v == "legacy" else "Modernized", key=f"edit-version-{epoch}")
                    save, remove = st.columns([2, 1])
                    if save.button("Save & reindex", type="primary", use_container_width=True):
                        mutate(workspace, lambda: workspace.upsert(title, content, system, document.source_type, selected),
                               "Document updated. The new content is now searchable.")
                    if remove.button("Remove source", use_container_width=True):
                        mutate(workspace, lambda: workspace.remove(selected), "Source and its chunks removed from the index.")
                with preview:
                    st.subheader("Live chunk preview")
                    st.caption("Your edits appear here before you publish them.")
                    parts = split_chunks([replace(document, text=content)], max_chars=workspace.chunk_size)
                    strip(parts)
                    st.caption(f"{len(parts)} chunks · {len(content):,} characters · {workspace.chunk_size:,} character limit")
                    chunk_cards(parts, 6)
                    if len(parts) > 6:
                        st.caption(f"Showing 6 of {len(parts)} chunks. Explore all chunks after saving.")
    with add:
        edit, preview = st.columns([1.4, 1], gap="large")
        with edit:
            st.subheader("Bring in a new source")
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
            text = st.text_area("New source content", key="draft_text", height=300, placeholder="Paste the evidence you want the assistant to use…")
            version, kind = st.columns(2)
            system = version.selectbox("New source version", ["legacy", "mod_v1"], format_func=lambda v: "Legacy" if v == "legacy" else "Modernized")
            source_type = kind.selectbox("Source type", ["doc", "email", "code", "ticket", "runbook"])
            if st.button("Publish to knowledge base →", type="primary", disabled=not title.strip() or not text.strip()):
                mutate(workspace, lambda: workspace.upsert(title, text, system, source_type),
                       "New evidence published. Ask your question again to use it.")
            st.button("Load AMI sample into editor", on_click=draft_sample)
        with preview:
            st.subheader("What the index will see")
            if text.strip():
                parts = split_chunks([preview_document(title, text, system)], max_chars=workspace.chunk_size)
                strip(parts)
                st.caption(f"{len(parts)} chunks ready to index · Preview only until published")
                chunk_cards(parts, 5)
            else:
                markup('<div class="empty-state"><b>Every source starts here.</b><p>Add content to see exact '
                       'chunk boundaries before it becomes searchable knowledge.</p></div>')
    with controls:
        reset, log = st.columns([1, 1.3], gap="large")
        with reset:
            st.subheader("A clean slate, on demand")
            st.write("Restore the checked-in corpus for another presentation, or clear the workspace to demonstrate ingestion from zero.")
            st.caption("These actions affect this session’s documents and search index. Original files remain intact. Earlier answers keep their revision labels.")
            if st.button("Restore baseline corpus", type="primary", use_container_width=True):
                mutate(workspace, workspace.reset, "Baseline restored. Ready for another run.")
            if st.button("Clear knowledge base", use_container_width=True):
                mutate(workspace, lambda: workspace.reset(empty=True), "Knowledge base cleared. Add evidence to begin.")
            st.download_button("Export workspace documents", json.dumps([asdict(d) for d in workspace.documents], indent=2),
                               file_name=f"continuity-revision-{workspace.revision}.json", mime="application/json", use_container_width=True)
        with log:
            st.subheader("Revision history")
            activity(workspace, 15)


def chunk_explorer(workspace):
    heading("02 / Inside the index", "One document. Every little detail.",
            "See exactly where a source becomes searchable passages. Preview a different chunk size, then rebuild the index live.")
    if not workspace.documents:
        st.info("The index is empty. Add a source in Knowledge base to visualize its chunks.")
        st.button("Add evidence →", on_click=go, args=("Knowledge base",))
        return
    source, size = st.columns([1.8, 1], gap="large")
    names = {d.chunk_id: d.section_title for d in workspace.documents}
    default = next((i for i, d in enumerate(workspace.documents) if len(d.text) > workspace.chunk_size * 1.5), 0)
    selected = source.selectbox("Explore a document", list(names), index=default, format_func=lambda key: names[key])
    document = next(d for d in workspace.documents if d.chunk_id == selected)
    chunk_size = size.slider("Maximum characters per chunk", 200, 3000, workspace.chunk_size, 100,
                             key=f"chunk-size-{workspace.revision}")
    parts = workspace.document_chunks(selected, chunk_size)
    changed = chunk_size != workspace.chunk_size
    a, b, c = st.columns([1, 1, 1.3])
    a.metric("Document length", f"{len(document.text):,}", help="Characters in the source document")
    b.metric("Preview chunks" if changed else "Indexed chunks", len(parts))
    c.metric("Boundary strategy", "Paragraph → line", help="No overlap. Split at paragraph or line boundaries when possible, then the character limit.")
    if changed:
        st.info(f"Previewing {chunk_size:,} characters. The live index still uses {workspace.chunk_size:,} until you rebuild.")
    if st.button("Apply chunk size & rebuild index", type="primary", disabled=not changed):
        mutate(workspace, lambda: workspace.rebuild(chunk_size), "Index rebuilt with the new chunk boundaries.")
    strip(parts)
    st.caption("Matching colors connect the source text to its chunks. Boundaries use characters, not model tokens; passages have no overlap.")
    left, right = st.columns([1.35, 1], gap="large")
    with left:
        st.subheader("The source")
        markup(f'<div class="mono" style="margin-bottom:10px">{esc(document.source_file)}</div>')
        markup('<div class="source-canvas">' + ''.join(
            f'<mark title="Chunk {i + 1}" style="background:{COLORS[i % len(COLORS)]}">{esc(part.text)}</mark>'
            for i, part in enumerate(parts)) + '</div>')
    with right:
        st.subheader("The chunks")
        st.caption(f"{len(parts)} exact passages · Each keeps its source and system version")
        with st.container(height=620, border=False):
            chunk_cards(parts)
        choice = st.selectbox("Inspect a full chunk", range(len(parts)), format_func=lambda i: f"Chunk {i + 1:02}")
        with st.expander("Full chunk text & metadata"):
            st.code(parts[choice].text, language="text", wrap_lines=True)
            st.json({"chunk_id": parts[choice].chunk_id, "system_version": document.system_version,
                     "source_type": document.source_type, "characters": len(parts[choice].text)})


def trace(result):
    diagnostic = result.get("diagnostics", {})
    candidates = result.get("retrieved_evidence", []) or result.get("evidence", [])
    st.subheader("Retrieval, in the open")
    st.caption("Actual ranked passages from this request. Scores are relevance scores, not confidence.")
    maximum = max((c.get("score") or 0 for c in candidates), default=1) or 1
    for i, candidate in enumerate(candidates):
        score = candidate.get("score") or 0
        markup(f'<div class="trace-row"><span class="trace-rank">{i + 1:02}</span><div class="trace-body">'
               f'<b>{esc(candidate.get("section_title", "Source"))}</b><div class="trace-bar"><i style="width:{max(0, min(100, score / maximum * 100)):.1f}%"></i></div>'
               f'</div><span class="trace-score">{score:.2f}</span></div>')
    if not candidates:
        st.caption("No relevant passages retrieved.")
    st.divider()
    for label, key in [("Retrieved", "retrieved_chunks"), ("Sent to model", "context_chunks"),
                       ("Prompt bytes", "prompt_bytes"), ("Generation attempts", "attempts")]:
        st.caption(f"{label}: {diagnostic.get(key, '—')}")
    st.caption(f"Stage: {diagnostic.get('stage', 'retrieval')}")
    if diagnostic.get("elapsed_seconds") is not None:
        st.caption(f"Elapsed: {diagnostic['elapsed_seconds']:.1f}s")
    with st.expander("Request diagnostics"):
        st.json(diagnostic)


def show_sources(entry):
    result = entry["result"]
    sources = result.get("evidence", []) or result.get("retrieved_evidence", [])
    st.markdown("##### Cited evidence" if result.get("evidence") else "##### Retrieved sources")
    for index, source in enumerate(sources):
        with st.expander(f"{index + 1:02} · {source.get('section_title', 'Source')} · {'Modernized' if source.get('system_version') == 'mod_v1' else 'Legacy'}"):
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
    st.caption(f"KB revision {entry['revision']:02} · {entry['scope']} · {len(result.get('evidence', []))} cited passages")


def live_qa(workspace):
    heading("03 / Evidence into answers", "Ask. Change the evidence. Ask again.",
            "Every answer is generated live from this workspace. Pin a baseline answer to make the impact of new knowledge visible.")
    st.session_state.setdefault("question", st.session_state.get("last_question", AMI_QUESTION))
    st.session_state.setdefault("scope", st.session_state.get("last_scope", "legacy"))
    st.session_state.setdefault("answers", [])
    with st.form("ask-form"):
        question = st.text_area("Your question", key="question", height=85)
        scope_col, action = st.columns([1, 2], vertical_alignment="bottom")
        scope = scope_col.selectbox("Evidence scope", ["legacy", "mod_v1", "compare"], key="scope",
                                    format_func=lambda v: {"legacy": "Legacy only", "mod_v1": "Modernized only", "compare": "Compare both systems"}[v])
        submitted = action.form_submit_button("Generate live answer ↗", type="primary", use_container_width=True)
    if submitted and question.strip():
        st.session_state.last_question = question
        st.session_state.last_scope = scope
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
    if not st.session_state.answers:
        markup('<div class="empty-state"><b>Let the evidence speak.</b><p>Start with the AMI question to reveal a knowledge gap. '
               'Then publish the owner clarification and watch a real model use the new source.</p></div>')
        st.button("Add the missing evidence →", on_click=draft_sample)
        return
    answers = st.session_state.answers
    index = st.selectbox("Answer history", range(len(answers) - 1, -1, -1),
                         format_func=lambda i: f"#{i + 1} · Rev {answers[i]['revision']:02} · {answers[i]['question'][:90]}")
    entry = answers[index]
    if entry["revision"] != workspace.revision:
        st.info(f"This answer used revision {entry['revision']:02}. The current KB is revision {workspace.revision:02}. Generate again to use current evidence.")
    main, detail = st.columns([1.8, 1], gap="large")
    with main:
        st.subheader("The answer")
        answer_body(entry)
        pin, update = st.columns(2)
        if pin.button("Pin as before", use_container_width=True):
            st.session_state.before_answer = entry
            st.rerun()
        update.button("Add new evidence +", on_click=draft_sample, use_container_width=True)
        before = st.session_state.get("before_answer")
        if before:
            with st.expander("Before & after", expanded=True):
                if before["id"] == entry["id"]:
                    st.info("Baseline pinned. Update the KB, then generate the same question again to compare.")
                elif before["question"] != entry["question"] or before["scope"] != entry["scope"]:
                    st.warning("These answers use different questions or scopes. Use the same inputs for a meaningful comparison.")
                first, second = st.columns(2)
                with first:
                    st.markdown(f"**Before · revision {before['revision']:02}**")
                    answer_body(before)
                with second:
                    st.markdown(f"**After · revision {entry['revision']:02}**")
                    answer_body(entry)
                if st.button("Unpin comparison"):
                    del st.session_state.before_answer
                    st.rerun()
        show_sources(entry)
    with detail:
        trace(entry["result"])


def run():
    st.set_page_config(page_title="Continuity · Live modernization studio", page_icon="◈", layout="wide", initial_sidebar_state="expanded")
    markup('<style>' + Path(__file__).with_name("ui.css").read_text(encoding="utf-8") + '</style>')
    if "workspace" not in st.session_state:
        with st.spinner("Preparing your live knowledge workspace…"):
            st.session_state.workspace = LiveWorkspace()
    workspace = st.session_state.workspace
    sidebar(workspace)
    page = st.session_state.page
    st.session_state.mobile_page = page
    with st.container(key="mobile_navigation"):
        st.selectbox("Navigate workspace", PAGES, key="mobile_page",
                     on_change=lambda: go(st.session_state.mobile_page))
    markup(f'<div class="topline"><span>Workspace &nbsp;/&nbsp; <strong>{esc(page)}</strong></span>'
           f'<span class="badge"><i class="dot"></i> LIVE WORKSPACE &nbsp;·&nbsp; REV {workspace.revision:02}</span></div>')
    if st.session_state.get("flash"):
        st.success(st.session_state.pop("flash"))
    {"Overview": overview, "Knowledge base": knowledge_base, "Chunk explorer": chunk_explorer, "Live Q&A": live_qa}[page](workspace)
