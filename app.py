import html
import sys
from pathlib import Path
from typing import Any
from urllib.parse import quote

import streamlit as st

from knowledge_assistant.core import KnowledgeAssistant, PIPELINE_VERSION
from knowledge_assistant.demo import DemoAssistant, SCENARIOS
from knowledge_assistant.llm_provider import ProviderError, load_provider_config


st.set_page_config(page_title="Continuity", page_icon="◈", layout="wide", initial_sidebar_state="collapsed")


def safe(value: object) -> str:
    return html.escape(str(value))


def scope_name(scope: str) -> str:
    return {"compare": "Compare systems", "legacy": "Legacy only", "mod_v1": "Modernized only"}[scope]


def document_url(chunk_id: object, query: str, source: dict | None = None) -> str:
    url = f"?citation={quote(str(chunk_id), safe='')}&question={quote(query, safe='')}"
    if st.session_state.get("guided_demo", False):
        url += "&demo=1"
    if source is not None and "excerpt_start" in source and "excerpt_end" in source:
        url += f"&start={int(source['excerpt_start'])}&end={int(source['excerpt_end'])}"
    return url


def full_source_text(source: Any) -> tuple[str, bool]:
    """Load the complete local source when it is available and text-readable."""
    source_path = Path(source.source_file)
    if source_path.is_file() and source_path.suffix.lower() != ".xlsx":
        try:
            return source_path.read_text(encoding="utf-8", errors="ignore"), True
        except OSError:
            pass
    return source.text, False


def highlight_indexed_section(document: str, indexed_text: str) -> str:
    """Highlight the exact record used for retrieval while keeping the full document readable."""
    if not indexed_text:
        return html.escape(document)
    start = document.find(indexed_text)
    if start < 0:
        return html.escape(document)
    end = start + len(indexed_text)
    return (
        html.escape(document[:start])
        + '<mark class="indexed-section">'
        + html.escape(document[start:end])
        + "</mark>"
        + html.escape(document[end:])
    )


def show_document_viewer(source: Any, question: str) -> None:
    version = "Modernized" if source.system_version == "mod_v1" else "Legacy"
    document, is_full_source = full_source_text(source)
    passage = source.text
    try:
        start = int(st.query_params.get("start", 0))
        end = int(st.query_params.get("end", len(passage)))
        if 0 <= start < end <= len(passage):
            passage = passage[start:end]
    except (TypeError, ValueError):
        pass
    back_url = "?demo=1" if st.session_state.get("guided_demo", False) else "?"
    st.markdown(f'<a class="back-link" href="{back_url}" target="_self">← Back to conversation</a>', unsafe_allow_html=True)
    st.markdown(f"## {safe(source.section_title)}")
    st.markdown(
        f'<div class="document-meta"><span>{safe(version)}</span><span>{safe(source.source_type.title())}</span>'
        f'<span>{safe(source.chunk_id)}</span></div>'
        f'<a class="source-path" href="{document_url(source.chunk_id, question)}" target="_blank" rel="noopener noreferrer">'
        f'{safe(source.source_file)}</a>',
        unsafe_allow_html=True,
    )
    st.markdown("### Source document")
    if is_full_source:
        st.caption("The highlighted section is the exact record used to ground the answer. The rest of this is the complete local source file.")
    else:
        st.caption("A complete local source file is not available for this record; this viewer shows the indexed record used to ground the answer.")
    st.markdown(
        f'<article class="document-text">{highlight_indexed_section(document, passage)}</article>',
        unsafe_allow_html=True,
    )
    actions, provenance = st.columns([1, 2])
    with actions:
        st.download_button(
            "Download source document",
            data=document,
            file_name=Path(source.source_file).name or f"{source.chunk_id}.txt",
            mime="text/plain",
            use_container_width=True,
        )
    with provenance:
        st.caption(
            f"Indexed from {source.source_file} · {source.date} · confidence {source.confidence_score:.0%}"
        )


def show_answer(summary: str) -> None:
    """Give version-comparison answers a scan-friendly, two-part reading flow."""
    if "Legacy:" in summary and "Modernized:" in summary:
        legacy, modernized = summary.split("Modernized:", maxsplit=1)
        legacy = legacy.removeprefix("Legacy:").strip()
        modernized = modernized.strip()
        st.markdown("##### What changed")
        legacy_column, modernized_column = st.columns(2, gap="small")
        with legacy_column:
            st.markdown(f'<div class="finding legacy"><span>Legacy</span><p>{safe(legacy)}</p></div>', unsafe_allow_html=True)
        with modernized_column:
            st.markdown(f'<div class="finding modernized"><span>Modernized</span><p>{safe(modernized)}</p></div>', unsafe_allow_html=True)
        return
    st.markdown(summary)


def show_evidence(evidence: list[dict[str, Any]], question: str, cited: bool = True) -> None:
    if not evidence:
        return

    st.markdown("##### Sources" if cited else "##### Retrieved sources")
    st.caption("Passages cited in this answer." if cited else "Relevant passages found by search. These are available to inspect even though there is no validated answer.")
    for index, source in enumerate(evidence, start=1):
        version = "Modernized" if source.get("system_version") == "mod_v1" else "Legacy"
        with st.container(border=True):
            source_info, action = st.columns([5, 1.2], vertical_alignment="center")
            with source_info:
                st.markdown(
                    f"**[{index}] {safe(source.get('section_title', source.get('chunk_id', 'Evidence')))}**  \n"
                    f"{safe(version)} · {safe(source.get('source_type', 'record')).title()} · "
                    f"`{safe(source.get('chunk_id', ''))}`  \n"
                    f'<a class="source-path source-list-path" href="{safe(document_url(source.get("chunk_id", ""), question, source))}" '
                    f'target="_blank" rel="noopener noreferrer">{safe(source.get("source", "Indexed record"))}</a>',
                    unsafe_allow_html=True,
                )
                st.caption(safe(source.get("note", "Retrieved evidence.")))
            with action:
                st.markdown(
                    f'<a class="view-record" href="{safe(document_url(source.get("chunk_id", ""), question, source))}" '
                    f'target="_blank" rel="noopener noreferrer">View document →</a>',
                    unsafe_allow_html=True,
                )


def show_result(result: dict, question: str) -> None:
    evidence = result.get("evidence", [])
    diagnostic = result.get("diagnostics", {})
    if result.get("status") == "error":
        st.error(result["summary"])
    else:
        show_answer(result["summary"])
    prepared = result.get("generation_method") == "prepared_demo"
    counts = (f"Prepared walkthrough · {len(evidence)} local sources · No model call"
              if prepared else f"{diagnostic.get('retrieved_chunks', len(evidence))} passages retrieved · {len(evidence)} cited")
    if diagnostic.get("elapsed_seconds") is not None:
        counts += f" · {diagnostic['elapsed_seconds']:.1f}s"
    st.caption(counts)
    show_evidence(evidence or result.get("retrieved_evidence", []), question, cited=bool(evidence))
    if diagnostic:
        with st.expander("Answer details"):
            st.json(diagnostic)
    elif not prepared:
        st.caption("This answer predates the current retrieval update. Submit the question again to regenerate it.")


st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
:root { --ink:#172033; --muted:#667085; --canvas:#f6f7fb; --line:#e6e8f0; --brand:#5b5ce2; --brand-pale:#f1f1ff; --green:#067647; }
html, body, [class*="css"] { font-family:Manrope, sans-serif; } .stApp { background:var(--canvas); color:var(--ink); }
[data-testid="stHeader"], [data-testid="stSidebar"] { display:none; } .block-container { max-width:980px; padding:1.25rem 1.25rem 7.5rem; }
.app-header { display:flex; align-items:center; justify-content:space-between; gap:1rem; padding:0 0 1rem; border-bottom:1px solid var(--line); margin-bottom:1.4rem; }
.brand { display:flex; align-items:center; gap:.65rem; font-weight:800; letter-spacing:-.035em; font-size:1.05rem; color:var(--ink); }.brand-mark { display:grid; place-items:center; width:32px; height:32px; border-radius:10px; color:#fff; background:linear-gradient(135deg,#7778f1,#3d3fbd); box-shadow:0 7px 16px rgba(76,78,206,.22); }.brand-sub { color:#98a2b3; font-weight:600; margin-left:.2rem; }
.live { color:var(--green); font-size:.74rem; font-weight:800; white-space:nowrap; }.live-dot { display:inline-block; width:7px; height:7px; border-radius:99px; background:#12b76a; margin-right:.35rem; box-shadow:0 0 0 3px #d1fadf; }
.welcome { padding:2.2rem .35rem 1.2rem; text-align:center; }.welcome h1 { margin:0; font-size:1.8rem; letter-spacing:-.055em; line-height:1.18; }.welcome p { max-width:570px; margin:.65rem auto 0; color:var(--muted); font-size:.9rem; line-height:1.6; }.context-note { color:var(--muted); font-size:.72rem; margin:0 0 .5rem; }
.result-meta { display:flex; align-items:center; gap:.5rem; flex-wrap:wrap; margin:.65rem 0 1rem; color:var(--muted); font-size:.72rem; font-weight:700; }.result-status { padding:.2rem .48rem; border-radius:99px; color:#3730a3; background:var(--brand-pale); }.suggestion { display:inline-block; color:#4747b7; background:#fff; border:1px solid #dfe1fb; border-radius:99px; padding:.36rem .66rem; margin:.35rem .2rem 0 0; font-size:.72rem; font-weight:700; }.finding { min-height:126px; box-sizing:border-box; padding:.9rem 1rem; border-radius:12px; border:1px solid var(--line); margin:.15rem 0 .85rem; }.finding span { display:block; margin-bottom:.45rem; color:#475467; font-size:.69rem; font-weight:800; letter-spacing:.08em; text-transform:uppercase; }.finding p { margin:0; color:#344054; font-size:.8rem; line-height:1.55; }.finding.legacy { background:#fffaf5; border-color:#f5dfca; }.finding.modernized { background:#f4f6ff; border-color:#dfe1fb; }.view-record,.back-link { display:inline-flex; align-items:center; justify-content:center; min-height:34px; box-sizing:border-box; border-radius:9px; text-decoration:none!important; font-size:.72rem; font-weight:800; }.view-record { width:100%; color:#4747b7!important; background:#fafaff; border:1px solid #dfe1fb; }.view-record:hover { background:#f0f0ff; }.back-link { color:#4747b7!important; margin:0 0 1.25rem; }.source-path { display:inline-block; max-width:100%; overflow:hidden; text-overflow:ellipsis; color:#475467!important; font-family:'DM Mono',monospace; font-size:.7rem; text-decoration:underline!important; text-decoration-color:#b9bce9!important; text-underline-offset:3px; white-space:nowrap; }.source-path:hover { color:#4747b7!important; }.source-list-path { margin-top:.2rem; }.document-meta { display:flex; gap:.45rem; flex-wrap:wrap; margin:.65rem 0 .45rem; }.document-meta span { color:#475467; background:#fff; border:1px solid var(--line); border-radius:99px; padding:.28rem .55rem; font-size:.7rem; font-weight:700; }.document-text { max-height:60vh; overflow:auto; box-sizing:border-box; padding:1.1rem 1.2rem; border:1px solid var(--line); border-radius:14px; background:#fff; color:#344054; font-family:'DM Mono',monospace; font-size:.78rem; line-height:1.7; white-space:pre-wrap; } mark.indexed-section { background:#fff1a8; color:inherit; border-radius:3px; box-shadow:0 0 0 2px rgba(245,158,11,.16); padding:.05rem .08rem; }
[data-testid="stChatMessage"] { border:1px solid var(--line); border-radius:16px; padding:1rem 1.05rem; margin-bottom:.9rem; background:#fff; box-shadow:0 2px 7px rgba(16,24,40,.025); } [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] { font-size:.88rem; line-height:1.65; } [data-testid="stVerticalBlockBorderWrapper"] { border-color:#e6e8f0!important; border-radius:11px!important; margin:.45rem 0!important; background:#fcfcfe!important; } [data-testid="stChatInput"] { position:fixed; bottom:1.25rem; left:50%; transform:translateX(-50%); width:min(920px, calc(100% - 2.5rem)); z-index:10; } [data-testid="stChatInput"] textarea { border-radius:14px!important; border:1px solid #cfd3e6!important; background:#fff!important; box-shadow:0 10px 30px rgba(16,24,40,.12)!important; } [data-testid="stPopover"] button { border-radius:9px!important; border:1px solid #dfe1fb!important; color:#4747b7!important; background:#fafaff!important; font-size:.72rem!important; font-weight:800!important; } [data-testid="stPopover"] button:hover { background:#f0f0ff!important; } [data-testid="stSelectbox"] { max-width:220px; }
@media(max-width:700px) { .block-container { padding:.9rem .8rem 7rem; } .brand-sub,.live { display:none; } .welcome { padding:1.5rem 0 .8rem; } .welcome h1 { font-size:1.45rem; } }
</style>
""",
    unsafe_allow_html=True,
)

guided_demo = st.toggle("Guided demo", value=st.query_params.get("demo") == "1" or "--demo" in sys.argv, key="guided_demo")
if guided_demo:
    assistant = DemoAssistant()
else:
    assistant = KnowledgeAssistant()
    try:
        active_provider = load_provider_config()
        provider_label = f"{active_provider.provider} · {active_provider.model}" if active_provider.provider != "none" else "No answer model configured"
    except ProviderError as provider_error:
        provider_label = f"Provider setup needed: {provider_error}"
    if assistant.provider_error:
        provider_label = f"Provider setup needed: {assistant.provider_error}"

if "messages" not in st.session_state:
    st.session_state.messages = []

st.markdown(
    f'<div class="app-header"><div class="brand"><span class="brand-mark">◈</span>Continuity <span class="brand-sub">Evidence assistant</span></div><div class="live"><span class="live-dot"></span>{len(assistant.chunks)} indexed records</div></div>',
    unsafe_allow_html=True,
)

requested_citation = str(st.query_params.get("citation", ""))
requested_question = str(st.query_params.get("question", ""))
if requested_citation:
    selected_source = next(
        (chunk for chunk in assistant.chunks if chunk.chunk_id == requested_citation),
        None,
    )
    if selected_source:
        show_document_viewer(selected_source, requested_question)
        st.stop()
    st.warning("That cited record is no longer in the current evidence index.")

if guided_demo:
    st.title("Modernization, with the evidence intact.")
    st.info("Prepared demo · Synthetic data · No model or API key required. "
            "The summaries and source selections are curated for this walkthrough; "
            "they are not live AI answers. Turn off Guided demo to use live Q&A.")
    scenario_index = st.selectbox("Demo scenario", range(len(SCENARIOS)),
                                  format_func=lambda index: SCENARIOS[index].title, key="demo_scenario")
    scenario = SCENARIOS[scenario_index]
    st.progress((scenario_index + 1) / len(SCENARIOS), text=f"Scenario {scenario_index + 1} of {len(SCENARIOS)}")
    st.caption(f"Evidence scope: {scope_name(scenario.scope)}")
    st.subheader(scenario.question)
    show_result(assistant.present(scenario), scenario.question)
    with st.expander("Presenter notes", expanded=True):
        st.write(scenario.takeaway)

    def move_demo(index: int) -> None:
        st.session_state.demo_scenario = index

    def run_demo_live() -> None:
        st.session_state.guided_demo = False
        st.query_params.pop("demo", None)
        st.session_state.pending_demo_question = (scenario.question, scenario.scope)
        st.session_state.evidence_scope = scenario.scope

    previous, following, restart, live = st.columns(4)
    previous.button("Previous", disabled=scenario_index == 0, on_click=move_demo, args=(scenario_index - 1,))
    following.button("Next scenario", disabled=scenario_index == len(SCENARIOS) - 1,
                     on_click=move_demo, args=(scenario_index + 1,))
    restart.button("Restart demo", on_click=move_demo, args=(0,))
    live.button("Ask live model", on_click=run_demo_live)
    st.stop()

controls, model = st.columns([1, 1])
with controls:
    scope = st.selectbox("Evidence scope", ["compare", "legacy", "mod_v1"], format_func=scope_name, label_visibility="collapsed", key="evidence_scope")
with model:
    st.markdown(f'<p class="context-note" style="text-align:right">Answer generation: {safe(provider_label)}</p>', unsafe_allow_html=True)

if not st.session_state.messages:
    st.markdown("""<div class="welcome"><h1>Ask across your modernization evidence.</h1><p>Answers are constrained to indexed records. Open the evidence drawer on any answer to inspect the exact records behind it.</p><span class="suggestion">Compare legacy and modernized renewal</span><span class="suggestion">Explain the surcharge conflict</span><span class="suggestion">Find AMI retry evidence</span></div>""", unsafe_allow_html=True)

for message_index, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            result = message.get("result", {"summary": message["content"], "status": "unsupported"})
            question = message.get("question", "")
            if not question and message_index > 0:
                question = st.session_state.messages[message_index - 1].get("content", "")
            show_result(result, question)
            if question and (result.get("status") == "error" or result.get("diagnostics", {}).get("pipeline_version") != PIPELINE_VERSION):
                if st.button("Regenerate answer", key=f"regenerate-{message_index}"):
                    with st.spinner("Retrieving evidence and generating an answer…"):
                        refreshed = assistant.answer_question(question, message.get("scope", scope))
                    message.update(content=refreshed["summary"], result=refreshed, question=question)
                    st.rerun()
        else:
            st.markdown(message["content"])

prompt = st.chat_input("Ask about a system, decision, or source…")
pending_demo = st.session_state.pop("pending_demo_question", None)
if pending_demo:
    prompt, scope = pending_demo
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Retrieving evidence…"):
            result = assistant.answer_question(prompt, scope)
        show_result(result, prompt)
    st.session_state.messages.append(
        {"role": "assistant", "content": result["summary"], "result": result, "question": prompt, "scope": scope}
    )
