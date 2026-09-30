import io
import stat
import zipfile

import pytest

from knowledge_assistant.codebase_import import ImportFile, prepare_codebase
from knowledge_assistant.llm_provider import ProviderConfig
from knowledge_assistant.workspace import LiveWorkspace


def make_zip(entries):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, text in entries:
            archive.writestr(name, text)
    return buffer.getvalue()


def test_zip_preserves_paths_and_reports_excluded_entries():
    link = zipfile.ZipInfo("repo/link.py")
    link.create_system = 3
    link.external_attr = (stat.S_IFLNK | 0o777) << 16
    preview = prepare_codebase([("repo.zip", make_zip([
        ("repo/src/Service.cs", "class Service {}"),
        ("repo/docs/README.md", "# Service design"),
        ("repo/node_modules/package/index.js", "dependency"),
        ("repo/.git/config", "git metadata"),
        ("repo/.env", "secret"),
        ("repo/.streamlit/secrets.toml", "secret"),
        ("../escaped.py", "pass"),
        ("C:/absolute.py", "pass"),
        ("repo/file.png", b"\x89PNG"),
        ("repo/binary.py", b"bad\x00content"),
        (link, "../target.py"),
    ]))])
    assert [f.path for f in preview.files] == ["repo/src/Service.cs", "repo/docs/README.md"]
    assert [f.source_type for f in preview.files] == ["code", "doc"]
    assert len(preview.skipped) == 9
    assert any(item["Reason"] == "Symbolic link" for item in preview.skipped)


def test_multiple_files_duplicates_oversize_and_bad_encoding():
    preview = prepare_codebase([
        ("app.py", b"print('hello')"), ("app.py", b"duplicate"),
        ("large.py", b"x" * 500_001), ("invalid.txt", b"\xff"), ("blank.md", b"  "),
    ])
    assert len(preview.files) == 1
    assert len(preview.skipped) == 4


def test_archive_and_file_count_errors_do_not_return_partial_preview():
    with pytest.raises(ValueError, match="Cannot read ZIP"):
        prepare_codebase([("bad.zip", b"not an archive")])
    with pytest.raises(ValueError, match="500 text files"):
        prepare_codebase([(f"source{i}.py", b"pass") for i in range(501)])


def test_import_reindexes_once_updates_matching_paths_and_keeps_other_sources(monkeypatch):
    workspace = LiveWorkspace(documents=[])
    monkeypatch.setattr(workspace._client, "get_max_batch_size", lambda: 2)
    files = [ImportFile("src/policy.py", "Zebra import requires two approvals.", "code"),
             ImportFile("src/other.cs", "class Other {}", "code"),
             ImportFile("docs/readme.md", "Project documentation.", "doc")]
    workspace.import_codebase(files, "Demo repo")
    assert workspace.revision == 2
    assert len(workspace.documents) == workspace.store.collection.count() == 3
    original_ids = {d.chunk_id for d in workspace.documents}
    workspace.import_codebase([ImportFile("src/policy.py", "Zebra import requires five approvals.", "code")], "Demo repo")
    assert workspace.revision == 3
    assert {d.chunk_id for d in workspace.documents} == original_ids
    candidates = workspace.assistant(provider_config=ProviderConfig())._retrieve_candidates("zebra import approvals", "legacy")
    assert any("five approvals" in c["text"] for c in candidates)
    assert not any("two approvals" in c["text"] for c in candidates)
    workspace.import_codebase([files[0]], "Demo repo", "mod_v1")
    assert len(workspace.documents) == 4
    assert {d.system_version for d in workspace.documents} == {"legacy", "mod_v1"}


def test_empty_batch_is_rejected_without_mutation():
    workspace = LiveWorkspace(documents=[])
    with pytest.raises(ValueError):
        workspace.import_codebase([], "Demo repo")
    assert workspace.revision == 1
