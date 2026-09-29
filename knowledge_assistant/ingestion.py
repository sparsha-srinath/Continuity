from __future__ import annotations

import json
import re
import zipfile
import xml.etree.ElementTree as ET
from posixpath import join as posix_join, normpath as posix_normpath
from pathlib import Path
from typing import List

from .models import SourceChunk
from .retrieval import split_chunks


def _default_seed_records() -> List[dict]:
    return [
        {
            "chunk_id": "ADR-006-001",
            "source_file": "ADR-006.md",
            "section_title": "Rate surcharge policy",
            "category": "policy",
            "access": "internal",
            "source_type": "doc",
            "entity": "RateCalculationEngine",
            "author": "E. Riley",
            "author_role_at_time": "Lead Architect",
            "date": "2016-11-04",
            "employment_status": "departed",
            "confidence_score": 0.86,
            "text": "The surcharge formula applies a fixed adjustment near the 1000 kWh threshold to preserve revenue stability for high-use accounts.",
            "keywords": ["surcharge", "1000", "threshold", "revenue"],
        },
        {
            "chunk_id": "TICKET-RATE-2231",
            "source_file": "Jira: RATE-2231",
            "section_title": "RATE-2231",
            "category": "ticket",
            "access": "internal",
            "source_type": "ticket",
            "entity": "RateCalculationEngine",
            "author": "D. Patel",
            "author_role_at_time": "Senior Analyst",
            "date": "2019-02-11",
            "employment_status": "active",
            "confidence_score": 0.91,
            "text": "Customer billing data showed a discontinuity in surcharge amounts around 1000 kWh; a temporary exception rule was added for near-threshold accounts.",
            "keywords": ["surcharge", "1000", "exception", "billing"],
        },
        {
            "chunk_id": "TICKET-RATE-2255",
            "source_file": "Jira: RATE-2255",
            "section_title": "RATE-2255",
            "category": "ticket",
            "access": "internal",
            "source_type": "ticket",
            "entity": "RateCalculationEngine",
            "author": "N. Gomez",
            "author_role_at_time": "Rate Engineer",
            "date": "2020-05-22",
            "employment_status": "departed",
            "confidence_score": 0.89,
            "text": "The threshold was widened to avoid customer complaints at 1000 kWh, but the logic was never reflected in the policy document.",
            "keywords": ["threshold", "complaints", "1000", "policy"],
        },
        {
            "chunk_id": "CODE-applySurcharge",
            "source_file": "src/rates/RateCalcService.py",
            "section_title": "applySurcharge()",
            "category": "code",
            "access": "internal",
            "source_type": "code",
            "entity": "applySurcharge",
            "author": "R. Nolan",
            "author_role_at_time": "Senior Developer",
            "date": "2021-07-10",
            "employment_status": "departed",
            "confidence_score": 0.97,
            "text": "if usage >= 1000 and usage < 1015: return base_rate * 1.08; else: return base_rate.",
            "keywords": ["applysurcharge", "1000", "usage", "base_rate"],
        },
        {
            "chunk_id": "AMI-001",
            "source_file": "MeterDataIntegration.md",
            "section_title": "Retry handling",
            "category": "policy",
            "access": "internal",
            "source_type": "doc",
            "entity": "MeterDataIntegration",
            "author": "R. Nolan",
            "author_role_at_time": "Integration Lead",
            "date": "2018-03-15",
            "employment_status": "departed",
            "confidence_score": 0.41,
            "text": "The integration retries failed meter uploads on a standard exponential backoff schedule.",
            "keywords": ["retry", "meter", "integration", "backoff"],
        },
        {
            "chunk_id": "AMI-002",
            "source_file": "Email: meter-integration-thread",
            "section_title": "Retry discussion",
            "category": "communications",
            "access": "internal",
            "source_type": "email",
            "entity": "MeterDataIntegration",
            "author": "M. Chen",
            "author_role_at_time": "Operations Analyst",
            "date": "2019-09-03",
            "employment_status": "active",
            "confidence_score": 0.53,
            "text": "We never documented the retry policy in a durable place; people relied on tribal memory and ad hoc scripts.",
            "keywords": ["retry", "documented", "tribal memory", "failed upload"],
        },
    ]


def _load_data_directory(base_dir: str | Path) -> List[dict]:
    base_path = Path(base_dir)
    if not base_path.exists():
        return _default_seed_records()

    structured_records_path = base_path / "demo_records.json"
    if structured_records_path.exists():
        try:
            records = json.loads(structured_records_path.read_text(encoding="utf-8"))
            if isinstance(records, list) and records:
                return records
        except json.JSONDecodeError:
            # Fall back to plain-text ingestion so a malformed demo file never blocks the app.
            pass

    records = []
    for file_path in sorted(base_path.glob("**/*.*")):
        if file_path.suffix.lower() not in {".txt", ".md", ".py"}:
            continue

        text = file_path.read_text(encoding="utf-8", errors="ignore")
        records.append(
            {
                "chunk_id": f"FILE-{file_path.stem.upper()}",
                "source_file": str(file_path),
                "section_title": file_path.stem,
                "category": "ingested",
                "access": "internal",
                "source_type": "doc",
                "entity": file_path.stem.replace("-", " ").title(),
                "author": "ingest-bot",
                "author_role_at_time": "Knowledge Pipeline",
                "date": "2026-09-22",
                "employment_status": "active",
                "confidence_score": 0.72,
                "text": text.strip(),
                "keywords": [token for token in file_path.stem.lower().replace("-", " ").split() if token],
            }
        )

    return records if records else _default_seed_records()


def build_seed_documents() -> List[SourceChunk]:
    records = _load_data_directory(Path(__file__).resolve().parent.parent / "data")
    chunks = []
    for record in records:
        chunks.append(
            SourceChunk(
                chunk_id=record["chunk_id"],
                source_file=record["source_file"],
                section_title=record["section_title"],
                category=record["category"],
                access=record["access"],
                source_type=record["source_type"],
                entity=record["entity"],
                author=record["author"],
                author_role_at_time=record["author_role_at_time"],
                date=record["date"],
                employment_status=record["employment_status"],
                confidence_score=float(record["confidence_score"]),
                text=record["text"],
                keywords=record.get("keywords", []),
                system_version=record.get("system_version", "legacy"),
                supersedes=record.get("supersedes"),
            )
        )
    root = Path(__file__).resolve().parent.parent
    chunks.extend(_load_blpts_folder(root / "blpts_legacy", "legacy"))
    chunks.extend(_load_blpts_folder(root / "blpts_mod", "mod_v1"))
    chunks.extend(_jira_ticket_chunks())
    return chunks


def build_seed_chunks() -> List[SourceChunk]:
    return split_chunks(build_seed_documents())


def _spreadsheet_text(path: Path) -> str:
    namespace = {
        "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
        "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
        "pkg": "http://schemas.openxmlformats.org/package/2006/relationships",
    }
    with zipfile.ZipFile(path) as workbook:
        shared_strings = []
        if "xl/sharedStrings.xml" in workbook.namelist():
            shared_root = ET.fromstring(workbook.read("xl/sharedStrings.xml"))
            shared_strings = [
                "".join(part.text or "" for part in item.findall(".//main:t", namespace))
                for item in shared_root.findall("main:si", namespace)
            ]
        workbook_root = ET.fromstring(workbook.read("xl/workbook.xml"))
        relation_root = ET.fromstring(workbook.read("xl/_rels/workbook.xml.rels"))
        targets = {}
        for item in relation_root.findall("pkg:Relationship", namespace):
            target = item.attrib["Target"].lstrip("/")
            if not target.startswith("xl/"):
                target = posix_join("xl", target)
            targets[item.attrib["Id"]] = posix_normpath(target)
        sheets = []
        for sheet in workbook_root.findall(".//main:sheet", namespace):
            sheet_name = sheet.attrib.get("name", "Sheet")
            relation_id = sheet.attrib[f"{{{namespace['rel']}}}id"]
            sheet_path = targets.get(relation_id)
            if not sheet_path or sheet_path not in workbook.namelist():
                continue
            sheet_root = ET.fromstring(workbook.read(sheet_path))
            rows = []
            for row in sheet_root.findall(".//main:sheetData/main:row", namespace):
                values = []
                for cell in row.findall("main:c", namespace):
                    value_node = cell.find("main:v", namespace)
                    value = value_node.text if value_node is not None else ""
                    if cell.attrib.get("t") == "s" and value:
                        value = shared_strings[int(value)]
                    elif cell.attrib.get("t") == "inlineStr":
                        value = "".join(node.text or "" for node in cell.findall(".//main:t", namespace))
                    values.append(value)
                rows.append("\t".join(values))
            sheets.append(f"Sheet: {sheet_name}\n" + "\n".join(rows))
    return "\n\n".join(sheets)


def _load_blpts_folder(folder: Path, system_version: str) -> List[SourceChunk]:
    version_label = "LEGACY" if system_version == "legacy" else "MOD"
    supported_extensions = {".csv", ".md", ".py", ".sql", ".txt", ".xlsx"}
    chunks = []
    for path in sorted(folder.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in supported_extensions or path.stat().st_size == 0:
            continue
        if path.suffix.lower() == ".xlsx":
            text = _spreadsheet_text(path)
        else:
            text = path.read_text(encoding="utf-8", errors="ignore").strip()
        if not text:
            continue

        relative_path = path.relative_to(folder).as_posix()
        normalized_path = re.sub(r"[^A-Z0-9]+", "-", relative_path.upper()).strip("-")
        preferred_ids = {
            ("legacy", "code/screen_license_renewal.py"): "BLPTS-LEGACY-FEE",
            ("legacy", "email/email_internal_fee_debate.txt"): "BLPTS-LEGACY-FEE-EMAIL",
            ("legacy", "email/client_correspondence_inspection_exemption.txt"): "BLPTS-LEGACY-CORRESPONDENCE",
            ("mod_v1", "code/fee_calculation.py"): "MOD-CODE-FEE",
            ("mod_v1", "code/inspection_rules.py"): "MOD-CODE-INSPECTION",
            ("mod_v1", "code/renewal_discount.py"): "MOD-CODE-DISCOUNT",
            ("mod_v1", "documents/release_notes_v1.md"): "MOD-DOC-RELEASE",
        }
        chunk_id = preferred_ids.get((system_version, relative_path), f"BLPTS-{version_label}-{normalized_path}")
        lower_path = relative_path.lower()
        source_type = "email" if "email" in lower_path else "ticket" if "jira_tickets" in lower_path else "spreadsheet" if path.suffix.lower() == ".xlsx" else "code" if path.suffix.lower() in {".py", ".sql"} else "doc"
        category = "communications" if source_type == "email" else "ticket" if source_type == "ticket" else "code" if source_type == "code" else source_type
        section_title = path.stem.replace("_", " ").replace("-", " ").title()
        heading = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        if heading:
            section_title = heading.group(1).strip()
        author_match = re.search(r"^(?:\*\*)?(?:Author|Document owner)(?:\*\*)?:\s*(.+)$", text, re.MULTILINE | re.IGNORECASE)
        date_match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", text)
        entity = "RenewalFeeCalculation" if system_version == "legacy" and ("fee" in lower_path or "license_renewal" in lower_path) else "fee_calculation" if "fee_calculation" in lower_path else "InspectionExemption" if "inspection" in lower_path else path.stem
        supersedes = "RenewalFeeCalculation" if system_version == "mod_v1" and entity == "fee_calculation" else None
        keywords = list(dict.fromkeys(re.findall(r"[a-z0-9]+", f"{path.stem} {text[:1200]}".lower())))[:40]
        chunks.append(SourceChunk(chunk_id=chunk_id, source_file=str(path), section_title=section_title, category=category, access="internal", source_type=source_type, entity=entity, author=author_match.group(1).strip("* ") if author_match else "Knowledge Pipeline", author_role_at_time="Document Owner" if author_match else "Knowledge Pipeline", date=date_match.group(1) if date_match else "2026-09-27", employment_status="active", confidence_score=0.96 if source_type in {"code", "ticket"} else 0.88, text=text, keywords=keywords, system_version=system_version, supersedes=supersedes))
    return chunks


def _jira_ticket_chunks() -> List[SourceChunk]:
    tickets = [
        ("KAN-4", "Inconsistent renewal fee for Home Occupation (type C) licenses", "During modernization discovery, QA identified that two type-C license renewals processed in 2019 were charged different fees ($50.00 and $75.00) despite matching license type and no documented rate change. Requesting engineering review of the fee calculation logic before modernization scope is finalized.", "legacy", "RenewalFeeCalculation", ["discovery", "legacy", "fee-calculation"]),
        ("KAN-5", "Unable to confirm rationale for inspection exemption on license types C and E", "Legacy system exempts Home Occupation (C) and Non-Profit (E) licenses from the 30-day post-application inspection rule. Resolution: R. Colston confirmed on 2026-03-11 that Ordinance 2009-14, Section 3(b), is the source.", "legacy", "InspectionExemption", ["discovery", "legacy", "inspection"]),
        ("KAN-6", "Consolidate fee calculation logic", "Consolidates both legacy fee paths into one unified fee_calculation.py module, resolving BLPTS-DISC-1 and applying the type-C surcharge consistently.", "mod_v1", "fee_calculation", ["modernization", "fee-calculation"]),
        ("KAN-7", "Implement multi-year renewal discount", "New feature with no legacy equivalent. Businesses may renew for 2 or 3 years at once, with a 5% or 10% discount respectively.", "mod_v1", "renewal_discount", ["modernization", "new-feature"]),
    ]
    return [SourceChunk(chunk_id=f"JIRA-{key}", source_file=f"Jira: {key}", section_title=summary, category="ticket", access="internal", source_type="ticket", entity=entity, author="BLPTS Project Team", author_role_at_time="Project Team", date="2026-09-27", employment_status="active", confidence_score=0.99, text=description, keywords=labels + ["BLPTS", key.lower()], system_version=version, supersedes="RenewalFeeCalculation" if key == "KAN-6" else None) for key, summary, description, version, entity, labels in tickets]
