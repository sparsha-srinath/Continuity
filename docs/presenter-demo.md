# Presenting the Continuity demo

Use [the complete presenter script and copy-and-paste reference](demo-sample-data.md) as the single source for narration, questions, document drafts, expected results, and effective dates.

## Preparation

Run `./run_demo.ps1 -Install` the first time, then `./run_demo.ps1 -Port 8512` when that port is available. Use the address printed by the launcher. Do not launch another instance on an occupied port. The current development instance uses http://127.0.0.1:8512.

Start your configured model before presenting and verify a question succeeds. The provider label is configuration information, not a health check. Document management and chunk previews work without a model; generated answers require one.

Restore the baseline before the demo to load the latest repository sources, including `blpts_legacy/documents/discovery_and_handover_handbook.md`. Keep the same browser tab throughout the presentation.

## Presentation order

1. **Opening:** introduce the two dummy BLPTS applications and frame the story as a PowerBuilder-to-.NET modernization in progress. The application previews are stand-ins for those technologies.
2. **Overview → Legacy application:** introduce licenses, renewals, fees, and inspections. The whole card opens the embedded interactive application preview.
3. **Return to Continuity overview → Modernized application:** show the corresponding web workflow, unified calculation, and multi-year renewal. Return to the same Continuity workspace.
4. **Knowledge base:** show the document inventory, source tags, and system versions.
5. **Chunk explorer:** use legacy `business_rules.py` for Python symbols, legacy `seed_data.sql` for statement packing, and **BLPTS discovery and handover handbook** for headings and paragraphs. Restore the 1,800-character limit before Q&A.
6. **PM gathering requirements:** explain the AMI retry feature. Generate the same question with **Modernized only** (no relevant policy evidence), **Legacy only** (basic backoff information but no exact values; pin this baseline), then **Compare both systems** (show the gap across versions). Return to Legacy only.
7. **PM asks the client:** the client responds with a four-retry clarification. Publish it as a Legacy document using the copy-and-paste reference.
8. **Live Q&A, after:** regenerate the same question, open **Before & after**, inspect the citation, and explain retrieval diagnostics.
9. **Document library:** update that existing clarification to five retries with **Save new revision & reindex**. Show **Source history**, effective dates, and the Sparsha author tag.
10. **Live Q&A, correction:** compare the four-retry answer with the new five-retry evidence.
11. **Modernized implementation evidence:** explain that the team has now implemented the confirmed requirement in the scenario. Publish the synthetic `AmiRetryPolicy.cs` sample as **Modernized / Code**. Publishing indexes the sample; it does not deploy or run it.
12. **Full circle:** ask the original AMI question with **Modernized only**, then compare both versions to trace the legacy requirement to the modernized policy. Close with why this is called Continuity: the next person can follow the knowledge from discovery through clarification, correction, and implementation.

The application previews use the existing repository HTML. The legacy preview is self-contained; the modernized preview loads Bootstrap assets from a CDN. Check both before presenting. No separate static server is required when opening them from Overview. Navigating back preserves the Continuity workspace; the embedded application preview itself may reset when reopened.

## Demonstration boundaries

All sample applications and source records are synthetic. Responses are generated live, so wording and scores vary. Search scores are relevance scores, not confidence percentages. Citation validation checks that a cited passage exists in the supplied evidence; it does not prove every claim is supported.

Python uses AST symbol boundaries. SQL packs adjacent statements within the selected maximum. Prose packs paragraphs within headings. Oversized units can still split. The explorer shows a preview until **Apply chunk size & rebuild index** is used. A stable chunk count does not necessarily mean the boundaries are unchanged.

The long handbook is proposed discovery guidance, not authoritative historical business-rule evidence. The AMI clarification is deliberately absent from the baseline. Do not publish it until the baseline answer has been generated and pinned.

Each browser session owns its documents and Chroma index. Source revisions, effective dates, and the demo author label illustrate provenance within that session; they are not a persistent production audit service or authenticated identity system. A new session or server restart can lose edits. Export documents before resetting if you need an archival copy.

## Other supported interactions

- Import a ZIP or multiple source files through **Knowledge base → Import codebase**. The importer reads text without executing it, preserves paths, and previews skipped files.
- Tag sources as documents, email, code, tickets, or other supported types.
- Filter the document library, inspect historical revisions, or export current workspace documents.
- Clear the knowledge base to demonstrate missing evidence, then restore it before another presentation.

Follow the detailed reference for exact field labels and copy-and-paste content rather than improvising new values during the live demonstration.
