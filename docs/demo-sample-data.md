# Continuity live demo: presenter script and copy-and-paste reference

Keep this reference beside Continuity. Use the updated running app at http://127.0.0.1:8512 (or the port printed by your launcher). Keep the same Continuity browser tab throughout the presentation so the workspace and pinned answers stay together. All application screens, records, and sample evidence here are synthetic; BLPTS is not a City of San Diego production application.

## Before the audience arrives

- Start the configured model and verify a Q&A request succeeds. The provider label alone does not confirm that the model is reachable.
- Open **Knowledge base → Reset & activity → Restore baseline corpus**. This discards earlier session edits, reloads the repository documents, and restores the 1,800-character limit. Do this before generating the baseline answer, never between the before and after questions.
- Confirm the library contains **BLPTS discovery and handover handbook**, from `blpts_legacy/documents/discovery_and_handover_handbook.md`. It is a long synthetic prose document for the chunking walkthrough. Restoring the baseline loads it into an existing session after the code update.
- Return to **Overview**. Verify both application cards open. The modernized preview uses Bootstrap assets from a CDN, so check its appearance before presenting.
- The exact model wording and relevance scores can vary. Present the evidence and any missing information rather than promising a particular generated sentence.

## Opening (about 60 seconds)

Before touching any screen:

> **SAY:** I’m using two dummy applications for this demonstration. They represent a fictional Business License & Permit Tracking System, or BLPTS. Staff use it to maintain license records, process renewals, calculate fees, and manage inspections.
>
> The legacy version is built in PowerBuilder and backed by older database logic. We are currently modernizing it into a .NET-based application. The screens are only one part of that effort. We also have to understand the business rules, the database behavior, the operating knowledge, and the decisions that were never fully documented.
>
> We work with the City of San Diego, and part of the work we do is supporting different applications, including modernizing older ones. This demo uses dummy applications, but it reflects the kind of discovery work that happens during a real modernization.
>
> I’ll quickly show the legacy application and the modernization target first. Then I’ll use Continuity to show how we inspect the code, SQL, and documents behind the applications; identify a missing answer; record a clarification; and make that knowledge available to the next person on the project.

Presenter note: the opening describes your work context. The following BLPTS examples are synthetic. This demo's knowledge changes persist within the browser session; do not describe it as a durable production knowledge service.

## 1. Overview → show the legacy and modernized applications

> **SAY:** Let’s start with the two applications. First is the legacy application, built in PowerBuilder.

**DO:** On Overview, click the **Legacy application** card. The whole card is clickable. No separate server or local file link is required.

> **SAY:** You can see how dated this interface looks. It is a desktop-style PowerBuilder application focused on the original operational workflow: looking up licenses and processing renewals. The fee calculation can follow different legacy paths, and the supporting rules are spread across screens, database logic, and older documentation. Rebuilding the screen alone doesn't explain all of that behavior.

**DO:** Show the renewal screen and the **C - Home Occupation** license type. Briefly point to the record, fee fields, and clerk workflow. If using the fee calculation controls, explain that the differing legacy paths are intentional demo material. Do not change or resolve their historical inconsistency during this walkthrough.

**DO:** Click **Return to Continuity overview**, then the **Modernized application** card. Show **Renewal**, then the documented rules. Return using **Return to Continuity overview**.

> **SAY:** Now this is the modernized .NET version, which is still in progress. The technology stack changes the experience and the capabilities: it is a web application with unified fee calculation, documented inspection rules, and multi-year renewals. Some changes are deliberate improvements that the new platform makes easier to deliver. Others must be traced back to legacy behavior and validated with evidence, so we know what to preserve, what to change, and what still needs clarification.

**Optional comparison inputs:** Type **C - Home Occupation**, renewal year **2026**, term **1 year** in the modernized calculator. The annual total is **$75**. Change to **3 years** to show the new multi-year feature: **$225 before discount**, **$22.50 discount**, **$202.50 final total**. These values come from the synthetic implementation. They are unrelated to the AMI scenario below.

## 2. Introduce the Continuity workspace

> **SAY:** This is the Continuity overview. The application cards give us the business context, and the workspace cards take us to the source documents, chunk explorer, and questions. I'll first show how the sources are prepared. Then we'll walk through a situation we actually run into on projects: a question comes up, the answer isn't documented yet, we get a clarification, and a later question can use that new information.

**DO:** Click the **Knowledge base** card. Briefly show source types and system versions in the library. Then open **Chunk explorer** using the sidebar. The library is the document inventory; the explorer shows the searchable passages made from one selected document.

## 3. Chunk explorer: code, SQL, and long prose (2 minutes)

Nothing needs to be pasted for this section. These three sources are in the baseline. Move the slider and release it to refresh the preview. A preview alone does not change retrieval.

### A. Python: preserve symbol boundaries

**DO:** In **Document to inspect**, choose the legacy **Business Rules** document ending in `blpts_legacy/code/business_rules.py`. Set the limit to **1,800**.

> **SAY:** Python is parsed using its syntax tree. The module description is one chunk and the complete fee-calculation function is another. We keep the symbol name and source lines, so the passage remains traceable to the code.

**SHOW:** **Boundary strategy: Python symbols**. Open **Full chunk text & metadata** and select the second chunk. Point to `business_rules.calculate_renewal_fee_db_side`, its function kind, and its source lines. At 1,800 characters this sample has two chunks: module information and the complete function.

**DO:** Change to **400**, then back to **1,800**.

> **SAY:** If a function exceeds the limit, it still has to split. Increasing the limit lets that function fit again. Separate functions do not merge just because there is spare space.

### B. SQL: pack complete statements together

**DO:** Choose the legacy **Seed Data** document ending in `blpts_legacy/code/db/seed_data.sql`. Set the limit to **500**, then **1,800**.

> **SAY:** SQL uses statement boundaries. A chunk can contain several adjacent statements if they fit. At a smaller limit we get more chunks; at a larger limit we can keep more statements together. Semicolons inside strings or comments don't count as statement endings.

**SHOW:** **SQL statements**. For this fixture, expect **7 chunks at 500** and **2 at 1,800**. Open a full chunk to show multiple `INSERT` statements. The card is only a short preview, so use the full-text expander to show all the statements. SQL Server `GO` batch boundaries remain separate. A statement larger than the limit still requires splitting.

### C. Prose: headings and paragraphs in a long document

**DO:** Choose **BLPTS discovery and handover handbook**. Its file is `blpts_legacy/documents/discovery_and_handover_handbook.md`. Set the limit to **400**, then **1,800**. Scroll through the chunk cards and inspect a chunk from **Review document structure before indexing**.

> **SAY:** This is a deliberately long discovery and handover document. Prose uses headings and paragraphs. Paragraphs from the same section can fit together, but a new heading starts a separate section. We keep the heading and line range with each passage. Changing the limit changes how much of a section fits together without rewriting the source.

**SHOW:** **Headings / paragraphs**, the heading labels, line ranges, and the source highlighting. The section about reviewing document structure contains several paragraphs, making the difference easy to see. The handbook describes a proposed discovery process; it does not supply missing application settings or resolve the demo's historical conflicts.

**DO:** Return the slider to **1,800**. If **Apply chunk size & rebuild index** is enabled, click it. If it is disabled, the live index already matches. Use the default limit for the Q&A sequence so you are changing the evidence rather than the chunking configuration between answers.

> **SAY:** These are indexed passages. For each question, retrieval selects relevant passages, and a separate context packer fits the selected evidence into the model request. The model does not receive the entire knowledge base.

## 4. Live Q&A orientation — choose the right evidence scope

> **SAY:** Before I start the AMI example, let me show how the Q&A scope works. The assistant can search the modernized application only, the legacy application only, or compare both. That matters because an answer should be based on the version of the system we are discussing.

**DO:** Open **Live Q&A**. Point to **Source scope** and briefly select each option without generating an answer:

- **Modernized only:** searches only the .NET modernization sources.
- **Legacy only:** searches only the PowerBuilder-era application, its database artifacts, and its historical documentation.
- **Compare both systems:** retrieves evidence from both versions and asks the model to label the differences by version.

> **SAY:** For a question about how the old system currently behaves, I use Legacy only. For a question about the target implementation, I use Modernized only. When the team needs to understand what changed during modernization, I use Compare both.

## 5. Live Q&A — before the clarification

> **SAY:** Now let’s say I’m a project manager gathering requirements for the AMI metering-integration feature. Before the team can rebuild it safely, we need to understand how the legacy system handles retries. This is a separate integration example in our sample knowledge base.
>
> I'll select Legacy only so we look at what's known about that version, generate the answer, and open the evidence it used.

**DO:** Open **Live Q&A**, choose **Legacy only** under **Source scope**, and paste this into **Your question**:

```text
What are the exact AMI meter retry limits and backoff timings?
```

Click **Generate answer**. Open **Cited evidence** or **Retrieved sources**, then click **Pin baseline**.

**Expected evidence:** **Retry handling** from `MeterDataIntegration.md` describes exponential backoff without exact settings. **Retry discussion** records the documentation gap. Explain that the sources do not establish the exact values. If the generated answer supplies unsupported numbers, call out the mismatch; do not present them as confirmed.

## 6. Add new evidence

> **SAY:** Once this question is raised, the PM takes that specific gap to the client—in our work, that may be the city—and asks the people who still have that information or locates it in their records. A few days later, the answer comes back, perhaps in an email.
>
> We capture that response as a source, identify the system it applies to, and publish it to the knowledge base.

**DO:** Open **Knowledge base → Add document**. Paste this into **New document title**:

```text
AMI retry configuration — owner clarification
```

Set **New source version** to **Legacy**, **Source type** to **Document**, and **Effective from** to **2026-09-29**. We are recording the response as a standalone clarification document; Email is also available for importing the original correspondence.

Paste the complete block into **New source content**:

```markdown
# AMI retry configuration — owner clarification

Synthetic demo update | Integration Operations | 2026-09-29

## Confirmed retry settings
The AMI meter upload integration retries a failed upload up to 4 times.
The delays before those retries are 5 seconds, 10 seconds, 20 seconds, and
40 seconds. After the fourth unsuccessful retry, the upload is moved to
the dead-letter queue and an operations alert is raised.

## Scope and provenance
These values describe the legacy AMI meter upload integration in this
synthetic demonstration. This note supplements MeterDataIntegration.md,
which describes exponential backoff without specific values. The earlier
email about missing durable documentation predates this clarification.
These settings do not describe BLPTS license renewals or inspections.

## Recovery
An operator reviews the dead-letter queue, fixes the underlying failure,
and replays the upload. Preserve the original upload identifier to avoid
duplicate meter readings. Alert ownership rests with Integration Operations.
```

Review **Chunk preview**, then click **Publish to knowledge base**. Wait for the confirmation directly below the button. Typing alone does not update the index.

> **SAY:** The new source is now indexed. The confirmation shows the new revision and indexed chunks, and the change is attributed to Sparsha in this demo.

## 7. Live Q&A — after the clarification

> **SAY:** A few weeks later, a different person on the team—who wasn't part of that exchange and doesn't know this was ever a question—asks the same thing.
>
> We can compare the earlier answer with one generated using the updated knowledge base. The earlier sources lacked the settings; now there is a clarification supporting the exact values, with a citation back to it.

**DO:** Return to **Live Q&A**, keep **Legacy only**, and generate the same question again:

```text
What are the exact AMI meter retry limits and backoff timings?
```

Open **Before & after**, then inspect the new citation. The evidence supports **4 retries**, with delays of **5, 10, 20, and 40 seconds**, followed by the dead-letter queue and an operations alert.

Show **Retrieval details** and click a circled **?** beside a score or parameter. Explain that relevance scores are search scores, not confidence percentages. Retrieved passages and passages sent to the model may differ because of the request-size budget.

## 8. Edit existing evidence — four retries become five

> **SAY:** Information also gets corrected as discovery continues. Suppose the client confirms that a later firmware update added a fifth retry. We'll update the existing clarification rather than publish a second competing note.
>
> The new revision records who changed it, when it applies, and what it replaces. The earlier source remains available in history while new questions use the current revision.

**DO:** Pin the four-retry answer as the new baseline. Open **Knowledge base → Document library**. Select the current **AMI retry configuration — owner clarification** source. Keep the title, **Legacy** version, and **Document** type. Set **Effective from** to **2026-09-30**.

Replace the entire **Source content** with this block:

```markdown
# AMI retry configuration — owner clarification

Synthetic demo update | Integration Operations | 2026-09-30

## Revised retry settings
Following the confirmed firmware update, the legacy AMI meter upload
integration now retries a failed upload up to 5 times. The delays before
those retries are 5 seconds, 10 seconds, 20 seconds, 40 seconds, and
80 seconds. After the fifth unsuccessful retry, the upload is moved to
the dead-letter queue and an operations alert is raised.

## Change history and scope
This revision replaces the prior setting of 4 retries, effective
2026-09-30. Integration Operations confirmed that the firmware update
added the fifth retry step. The earlier four-retry guidance is historical.
This applies only to the legacy AMI meter upload integration in this
synthetic demonstration. It supplements MeterDataIntegration.md and does
not describe BLPTS license renewals or inspections.

## Recovery
Integration Operations reviews the dead-letter queue, resolves the
failure, and replays the upload using its original identifier to prevent
duplicate meter readings. Alert ownership remains with Integration Operations.
```

Open **Preview chunks**, then click **Save new revision & reindex**. This is the edit action; do not use Add document or Publish for this step.

**DO:** Select the newest clarification in the library and open **Source history**. Point to the current and replaced revisions, effective dates, **Changed by: Sparsha**, and the replaced source identifier. Under **Reset & activity**, show the Sparsha tag on the revision event if useful.

**DO:** Return to **Live Q&A** and generate the same question once more:

```text
What are the exact AMI meter retry limits and backoff timings?
```

Open **Before & after**. Compare **4 retries** in the pinned answer with **5 retries** and **5/10/20/40/80-second delays** in the current evidence. Historical answers retain their original evidence snapshot; generating again uses the current index.

> **SAY:** The team can work from the updated understanding and still inspect what changed. We haven't lost the earlier source or left two current documents contradicting each other.

## Close the loop — connect the applications, evidence, and current guidance

Choose **Compare both systems** and paste:

```text
How do BLPTS license renewal fees differ between the legacy and modernized systems?
```

Or:

```text
How do BLPTS inspection rules differ between the legacy and modernized systems?
```

Inspect the system-version labels and source citations. These questions connect the application previews to the indexed implementation and documentation. Do not expect fixed wording.

> **SAY:** We started with a legacy PowerBuilder application and its .NET modernization target. We then looked at how Continuity keeps code, SQL, and operational documents in useful searchable passages. When the AMI answer was missing, the system showed the gap instead of inventing an answer. Once we received a clarification, we recorded it, cited it, and then revised it when the understanding changed.
>
> That brings us full circle: the applications give us the business context, the evidence explains their behavior, and the knowledge workspace makes the team’s learning available to the next person working on the modernization.

## Reset after the presentation

Use **Knowledge base → Reset & activity → Restore baseline corpus** when ready to discard the demo edits. This restores the original corpus, including the long handbook, and the default chunk size. Older answers may remain visible in history with their original revision; generate a new baseline answer for the next presentation.

If you want to keep the session's documents first, use **Export workspace documents**. The export is an archival snapshot, not an automatic restore format. The in-session author tag is the demo identity, not proof of authenticated user attribution.
