"""Prepared presentation scenarios, separate from live retrieval and generation."""

from dataclasses import dataclass

from .ingestion import build_seed_chunks


@dataclass(frozen=True)
class DemoScenario:
    title: str
    question: str
    scope: str
    summary: str
    takeaway: str
    sources: tuple[tuple[str, str], ...]
    status: str = "supported"


SCENARIOS = (
    DemoScenario(
        "1. Resolve a renewal fee conflict",
        "How did modernization resolve the inconsistent type-C renewal fee?",
        "compare",
        "Legacy: Type-C renewals in 2019 could cost $50 through the database path or $75 "
        "through the renewal screen. The 2018 screen-only patch added a $25 surcharge, "
        "leaving two divergent implementations.\n\n"
        "Modernized: The unified fee_calculation.py applies the $25 type-C surcharge "
        "to the $50 base fee, producing $75 consistently.",
        "Open the legacy screen and modernized code. Explain why preserving the reason "
        "for a change matters as much as moving the code.",
        (
            ("JIRA-KAN-4", "different fees ($50.00 and $75.00)"),
            ("BLPTS-LEGACY-FEE", "Did not update business_rules.py"),
            ("MOD-CODE-FEE", 'if license_type == "C":'),
        ),
        "versioned",
    ),
    DemoScenario(
        "2. Recover the inspection rationale",
        "Why are license types C and E exempt from inspections, and was that preserved?",
        "compare",
        "Legacy: The County Clerk's March 11, 2026 correspondence confirms that "
        "Ordinance 2009-14, Section 3(b), exempts Home Occupation (C) and Non-Profit (E) "
        "from the standard 30-day inspection requirement. The email says the ordinance "
        "scan is not included in this export.\n\n"
        "Modernized: inspection_rules.py preserves the C/E exemption and records the "
        "ordinance reference explicitly.",
        "Open the correspondence, then the modernized rule. The source is the clerk's "
        "confirmation; the underlying ordinance scan is not in the corpus.",
        (
            ("BLPTS-LEGACY-CORRESPONDENCE", "Confirmed: Ordinance 2009-14"),
            ("MOD-CODE-INSPECTION", 'EXEMPT_LICENSE_TYPES = ("C", "E")'),
        ),
        "versioned",
    ),
    DemoScenario(
        "3. Expose stale surcharge documentation",
        "Why does the surcharge logic look inconsistent near 1000 kWh?",
        "legacy",
        "The policy describes a fixed adjustment near 1000 kWh, while the code applies "
        "an 8% multiplier only when usage is at least 1000 and below 1015. A later ticket "
        "says the threshold was widened without updating the policy. These records "
        "show documentation drift; they do not establish which rule is currently approved.",
        "Compare policy, change ticket, and code. Highlight the unresolved approval "
        "question before proposing a modernization decision.",
        (
            ("ADR-006-001", "fixed adjustment"),
            ("TICKET-RATE-2255", "never reflected in the policy document"),
            ("CODE-applySurcharge", "usage >= 1000 and usage < 1015"),
        ),
    ),
    DemoScenario(
        "4. Surface a knowledge gap",
        "What are the exact AMI meter retry limits and backoff timings?",
        "legacy",
        "The indexed AMI note mentions exponential backoff, but gives no exact retry "
        "limit or timing values. The email says the policy was never documented durably. "
        "These sources cannot establish the requested settings. Obtain the active "
        "integration configuration or implementation and confirm it with the owner.",
        "Show that missing evidence is a useful outcome: the assistant should expose "
        "what still needs discovery instead of inventing retry settings.",
        (
            ("AMI-001", "standard exponential backoff schedule"),
            ("AMI-002", "never documented the retry policy"),
        ),
        "gap",
    ),
)


class DemoAssistant:
    """Read actual local passages without initializing a model or persistent stores."""

    def __init__(self):
        self.chunks = build_seed_chunks()

    def present(self, scenario: DemoScenario) -> dict:
        evidence = []
        for source_id, required_text in scenario.sources:
            chunk = next((c for c in self.chunks
                          if (c.chunk_id == source_id or c.chunk_id.startswith(source_id + "::part-"))
                          and required_text in c.text), None)
            if chunk is None:
                return {"status": "error", "summary": "A prepared demo source is missing or changed. "
                        "Review the scenario before presenting it.", "evidence": [],
                        "generation_method": "prepared_demo"}
            evidence.append({
                "chunk_id": chunk.chunk_id, "source": chunk.source_file,
                "source_type": chunk.source_type, "section_title": chunk.section_title,
                "system_version": chunk.system_version, "details": chunk.text,
                "excerpt_start": 0, "excerpt_end": len(chunk.text),
                "note": "Local source selected for this prepared walkthrough.",
            })
        return {"status": scenario.status, "summary": scenario.summary,
                "evidence": evidence, "generation_method": "prepared_demo"}
