"""Bounded, in-memory previews of uploaded source trees. Never extracts or runs files."""

import io
import stat
import zipfile
from dataclasses import dataclass, field
from pathlib import PurePosixPath


MAX_FILE_BYTES = 500_000
MAX_TOTAL_BYTES = 10_000_000
MAX_FILES = 500
EXTENSIONS = set("txt md rst py sql csv json cs csproj sln vb vbproj fs fsproj js ts jsx tsx java kt go rs rb php c cpp h hpp html css scss xml xaml yaml yml toml ini config properties sh ps1 bat vue svelte gradle tf proto graphql".split())
EXCLUDED_DIRS = {".git", ".svn", ".hg", ".venv", "venv", "node_modules", "vendor", "bin", "obj",
                 "dist", "build", "target", "coverage", "__pycache__", ".next", ".idea", "__macosx"}


@dataclass(frozen=True)
class ImportFile:
    path: str
    text: str
    source_type: str


@dataclass
class ImportPreview:
    files: list[ImportFile] = field(default_factory=list)
    skipped: list[dict] = field(default_factory=list)


def path_issue(name):
    path = PurePosixPath(name.replace("\\", "/"))
    if path.is_absolute() or ".." in path.parts or any(":" in part for part in path.parts):
        return "Unsafe path"
    if not path.name or path.name == ".":
        return "Empty path"
    if any(part.lower() in EXCLUDED_DIRS for part in path.parts[:-1]):
        return "Dependency, build output, or repository metadata"
    lower = path.name.lower()
    if (lower.startswith((".env", "secrets.", "credentials.", "id_rsa", "id_ed25519"))
            or lower in {".npmrc", ".pypirc", "nuget.config"}
            or path.suffix.lower() in {".pem", ".key", ".pfx", ".p12"}):
        return "Credential or secret file name"
    if path.suffix.lower().lstrip(".") not in EXTENSIONS and lower not in {"dockerfile", "makefile", "license", "readme"}:
        return "Unsupported or binary file type"
    return None


def prepare_codebase(uploads: list[tuple[str, bytes]]) -> ImportPreview:
    if sum(len(data) for _, data in uploads) > 20_000_000:
        raise ValueError("Keep the combined upload below 20 MB. Split larger codebases into smaller batches.")
    preview = ImportPreview()
    seen = set()
    total = 0

    def skip(name, reason):
        preview.skipped.append({"Path": name, "Reason": reason})

    def accept(name, size, read):
        nonlocal total
        issue = path_issue(name)
        if issue:
            skip(name, issue)
            return
        normalized = PurePosixPath(name.replace("\\", "/")).as_posix()
        if normalized in seen:
            skip(name, "Duplicate path in this upload")
            return
        if size > MAX_FILE_BYTES:
            skip(name, "File exceeds 500 KB")
            return
        if len(preview.files) >= MAX_FILES or total + size > MAX_TOTAL_BYTES:
            raise ValueError("Import supports up to 500 text files and 10 MB of expanded source per batch. Split this upload.")
        try:
            raw = read()
            text = raw.decode("utf-8-sig")
        except UnicodeError:
            skip(name, "Not UTF-8 text")
            return
        if b"\x00" in raw:
            skip(name, "Binary content")
            return
        if not text.strip():
            skip(name, "Empty file")
            return
        suffix = PurePosixPath(normalized).suffix.lower()
        kind = "doc" if suffix in {".txt", ".md", ".rst", ".csv"} else "code"
        preview.files.append(ImportFile(normalized, text, kind))
        seen.add(normalized)
        total += len(raw)

    for name, data in uploads:
        if not name.lower().endswith(".zip"):
            accept(name, len(data), lambda data=data: data)
            continue
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                entries = archive.infolist()
                if len(entries) > 5000:
                    raise ValueError("Archive has more than 5,000 entries. Exclude dependencies and build output first.")
                for info in entries:
                    if info.is_dir():
                        continue
                    if stat.S_ISLNK(info.external_attr >> 16):
                        skip(info.filename, "Symbolic link")
                    elif info.flag_bits & 1:
                        skip(info.filename, "Encrypted archive entry")
                    else:
                        accept(info.filename, info.file_size, lambda info=info: archive.read(info))
        except (zipfile.BadZipFile, NotImplementedError, RuntimeError, EOFError) as error:
            raise ValueError(f"Cannot read ZIP {name}: {error}") from error
    return preview
