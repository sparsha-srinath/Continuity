"""Source-preserving structural boundaries. Parsing never executes source code."""

import ast
import re
from bisect import bisect_right
from dataclasses import dataclass, replace
from pathlib import Path


@dataclass(frozen=True)
class Region:
    start: int
    end: int
    kind: str = ""
    name: str = ""


def python_regions(text, module):
    tree = ast.parse(text)
    offsets = [0]
    for line in text.splitlines(keepends=True):
        offsets.append(offsets[-1] + len(line))
    definitions = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)

    def visit(node, start, end, name, kind):
        # Find direct lexical child definitions, including those inside control flow.
        def children(parent):
            for child in ast.iter_child_nodes(parent):
                if isinstance(child, definitions):
                    yield child
                else:
                    yield from children(child)

        cursor = start
        for child in sorted(children(node), key=lambda item: item.lineno):
            first_line = min([child.lineno] + [d.lineno for d in child.decorator_list])
            child_start = offsets[first_line - 1]
            child_end = offsets[child.end_lineno]
            if child_start > cursor:
                yield Region(cursor, child_start, kind, name)
            child_kind = "class" if isinstance(child, ast.ClassDef) else "function"
            yield from visit(child, child_start, child_end, f"{name}.{child.name}", child_kind)
            cursor = child_end
        if cursor < end:
            yield Region(cursor, end, kind, name)

    return list(visit(tree, 0, len(text), module, "module"))


def prose_regions(text):
    """Markdown headings, Setext/RST headings, paragraphs, and fenced blocks."""
    lines = text.splitlines(keepends=True)
    regions = []
    start = offset = 0
    heading = ""
    fence = None
    for index, line in enumerate(lines):
        stripped = line.strip()
        marker = re.match(r"^(`{3,}|~{3,})", stripped)
        if fence:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence):
                fence = None
        elif marker:
            fence = marker[1]
        else:
            atx = re.match(r"^ {0,3}#{1,6}\s+(.+?)\s*#*\s*$", line)
            underlined = (bool(stripped) and index + 1 < len(lines)
                          and re.fullmatch(r"[ \t]*([=~^`:\"+*#-])\1{2,}[ \t]*", lines[index + 1].rstrip("\r\n")))
            if atx or underlined:
                if start < offset:
                    regions.append(Region(start, offset, "heading", heading))
                start = offset
                heading = atx[1] if atx else stripped
            elif not stripped:
                regions.append(Region(start, offset + len(line), "heading", heading))
                start = offset + len(line)
        offset += len(line)
    if start < len(text):
        regions.append(Region(start, len(text), "heading", heading))
    return regions


def sql_regions(text):
    """Split terminators outside SQL strings/comments and dollar-quoted bodies."""
    regions = []
    start = pos = 0
    length = len(text)
    while pos < length:
        if pos == 0 or text[pos - 1] == "\n":
            batch = re.match(r"[ \t]*GO(?:[ \t]+\d+)?[ \t]*(?:--[^\n]*)?(?:\r?\n|$)", text[pos:], re.I)
            if batch:
                pos += batch.end()
                regions.append(Region(start, pos, "batch", f"Statement {len(regions) + 1}"))
                start = pos
                continue
        if text.startswith("--", pos):
            end = text.find("\n", pos + 2)
            pos = length if end < 0 else end + 1
        elif text.startswith("/*", pos):
            depth = 1
            pos += 2
            while pos < length and depth:
                if text.startswith("/*", pos):
                    depth += 1
                    pos += 2
                elif text.startswith("*/", pos):
                    depth -= 1
                    pos += 2
                else:
                    pos += 1
            if depth:
                raise ValueError("Unclosed SQL comment")
        elif text[pos] in "'\"`[":
            quote = "]" if text[pos] == "[" else text[pos]
            pos += 1
            while pos < length:
                if text[pos] == quote:
                    if pos + 1 < length and text[pos + 1] == quote:
                        pos += 2
                        continue
                    pos += 1
                    break
                pos += 1
            else:
                raise ValueError("Unclosed SQL quote")
        elif text[pos] == "$" and (tag := re.match(r"\$(?:[A-Za-z_][A-Za-z_0-9]*)?\$", text[pos:])):
            end = text.find(tag[0], pos + len(tag[0]))
            if end < 0:
                raise ValueError("Unclosed SQL dollar quote")
            pos = end + len(tag[0])
        elif text[pos] == ";":
            pos += 1
            while pos < length and text[pos].isspace():
                pos += 1
            regions.append(Region(start, pos, "statement", f"Statement {len(regions) + 1}"))
            start = pos
        else:
            pos += 1
    if start < length:
        regions.append(Region(start, length, "statement", f"Statement {len(regions) + 1}"))
    return regions


def bounded_ranges(text, start, end, limit):
    while start < end:
        stop = min(start + limit, end)
        if stop < end:
            boundary = text.rfind("\n\n", start + limit // 2, stop)
            if boundary < 0:
                boundary = text.rfind("\n", start + limit // 2, stop)
            if boundary >= 0:
                stop = boundary + 1
        yield start, stop
        start = stop


def split_source(source, max_chars):
    text = source.text
    suffix = Path(source.source_file.replace("\\", "/")).suffix.lower()
    language = {".py": "python", ".pyi": "python", ".sql": "sql"}.get(suffix, "text")
    strategy = "text-fallback"
    regions = [Region(0, len(text))]
    try:
        if language == "python":
            regions = python_regions(text, Path(source.source_file).stem)
            strategy = "python-ast"
        elif language == "sql":
            regions = sql_regions(text)
            strategy = "sql-statements"
        elif suffix in {".md", ".rst", ".txt"} or (not suffix and source.source_type in {"doc", "email"}):
            regions = prose_regions(text)
            strategy = "prose-structure"
    except (SyntaxError, ValueError, RecursionError):
        # Incomplete uploads and unsupported syntax remain searchable as exact text.
        regions = [Region(0, len(text))]
    if strategy in {"prose-structure", "sql-statements"}:
        packed = []
        for region in regions:
            compatible = (packed and (packed[-1].name == region.name if strategy == "prose-structure"
                                      else packed[-1].kind != "batch"))
            if compatible and region.end - packed[-1].start <= max_chars:
                packed[-1] = replace(packed[-1], end=region.end, kind=region.kind)
            else:
                packed.append(region)
        regions = packed
    line_starts = [0] + [m.end() for m in re.finditer("\n", text)]
    result = []
    for region in regions:
        for start, end in bounded_ranges(text, region.start, region.end, max_chars):
            part = len(result)
            result.append(replace(
                source,
                chunk_id=source.chunk_id if part == 0 else f"{source.chunk_id}::part-{part + 1}",
                text=text[start:end],
                section_title=source.section_title if part == 0 else f"{source.section_title} (continued {part + 1})",
                chunk_strategy=strategy, language=language,
                symbol_name=region.name if language == "python" else "",
                symbol_kind=region.kind if language == "python" else "",
                heading=region.name if strategy == "prose-structure" else "",
                line_start=bisect_right(line_starts, start),
                line_end=bisect_right(line_starts, max(start, end - 1)),
            ))
    return result
