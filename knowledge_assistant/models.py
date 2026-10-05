from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class SourceChunk:
    chunk_id: str
    source_file: str
    section_title: str
    category: str
    access: str
    source_type: str
    entity: str
    author: str
    author_role_at_time: str
    date: str
    employment_status: str
    confidence_score: float
    text: str
    keywords: List[str] = field(default_factory=list)
    system_version: str = "legacy"
    supersedes: str | None = None
    effective_from: str = ""
    effective_to: str | None = None
    revision_of: str | None = None
    revision_number: int = 1
    changed_by: str = ""
    changed_at: str = ""


@dataclass
class ConflictRecord:
    entity: str
    conflict_type: str
    description: str
    chunk_ids: List[str] = field(default_factory=list)
    system_version: str = "legacy"
