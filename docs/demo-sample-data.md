# Continuity live demo: presenter script and copy-and-paste reference

Keep this reference beside Continuity. Use the updated running app at http://127.0.0.1:8512 (or the port printed by your launcher). Keep the same Continuity browser tab throughout the presentation so the workspace and pinned answers stay together. All application screens, records, and sample evidence here are synthetic; BLPTS is not a City of San Diego production application.

## Demo sequence at a glance

1. Show the two dummy applications: the dated legacy interface and the in-progress modernization target.
2. Demonstrate Python, SQL, and prose in Chunk explorer.
3. [Start as the PM gathering AMI retry requirements](#4-live-qa-find-the-missing-ami-requirements): generate the same question with Modernized only, Legacy only, and Compare both systems.
4. [Ask the client and publish their response](#5-client-clarification-add-the-response-as-legacy-evidence): capture four retries as Legacy evidence, then ask again.
5. [Edit the same source after a client correction](#7-client-correction-edit-the-existing-document): five retries, with revision history.
6. [Record the modernized implementation](#8-implement-the-requirement-in-the-modernized-application): publish the C# sample as Modernized evidence, ask Modernized only, then compare both.
7. Close on Continuity: knowledge carried from discovery through clarification, correction, implementation, and handover.

## Before the audience arrives

- Start the configured model and verify a Q&A request succeeds. The provider label alone does not confirm that the model is reachable.
- Open **Knowledge base → Reset & activity → Restore baseline corpus**. This discards earlier session edits, reloads the repository documents, and restores the 1,800-character limit. Do this before generating the baseline answer, never between the before and after questions.
- Confirm the library contains **BLPTS discovery and handover handbook**, from `blpts_legacy/documents/discovery_and_handover_handbook.md`. It is a long synthetic prose document for the chunking walkthrough. Restoring the baseline loads it into an existing session after the code update.
- Return to **Overview**. Verify both application cards open. The modernized preview uses Bootstrap assets from a CDN, so check its appearance before presenting.
- The exact model wording and relevance scores can vary. Present the evidence and any missing information rather than promising a particular generated sentence.

## Opening (about 60 seconds)

Before touching any screen:

> **SAY:** I'm using two dummy applications for this demo. They show a Business License and Permit Tracking System. Staff use it to look up licenses, process renewals, calculate fees, and manage inspections.
>
> Let's say the old application was built in PowerBuilder, and we're now rebuilding it in .NET. We need to understand what the old system does and decide what the new one should do.
>
> We work with the City of San Diego, supporting applications and modernizing older ones. These are dummy applications, but the questions we'll look at are the kind we come across in that work.
>
> I'll show both applications first. Then we'll look at their code and documents, ask a question, and add the answer when we get it from the client.

Presenter note: the opening describes your work context. The following BLPTS examples are synthetic. This demo's knowledge changes persist within the browser session; do not describe it as a durable production knowledge service.

## 1. Overview → show the legacy and modernized applications

> **SAY:** Let's open the legacy application. This stands in for our old PowerBuilder system.

**DO:** On Overview, click the **Legacy application** card. The whole card is clickable. No separate server or local file link is required.

> **SAY:** You can see how dated it looks. A clerk uses this screen to look up a license and process a renewal. Some fee rules are in the screen code and others are in the database. We need to check both to understand how the total is calculated.

**DO:** Show the renewal screen and the **C - Home Occupation** license type. Briefly point to the record, fee fields, and clerk workflow. If using the fee calculation controls, explain that the differing legacy paths are intentional demo material. Do not change or resolve their historical inconsistency during this walkthrough.

**DO:** Click **Return to Continuity overview**, then the **Modernized application** card. Show **Renewal**, then the documented rules. Return using **Return to Continuity overview**.

> **SAY:** This is our example of the .NET version, which is still in progress. It looks different, and some of the features have changed too. It uses one fee calculation, explains the inspection rules, and lets people renew for more than one year. Those are choices the team has made during the rebuild. Moving to a new technology doesn't tell us which rules should change. We still need to confirm that with the client.

**Optional comparison inputs:** Type **C - Home Occupation**, renewal year **2026**, term **1 year** in the modernized calculator. The annual total is **$75**. Change to **3 years** to show the new multi-year feature: **$225 before discount**, **$22.50 discount**, **$202.50 final total**. These values come from the synthetic implementation. They are unrelated to the AMI scenario below.

## 2. Introduce the Continuity workspace

> **SAY:** Back here, we can open the documents, look at how they are split into chunks, or ask questions. I'll show the chunks first, then walk through a question where we need more information from the client.

**DO:** Click the **Knowledge base** card. Briefly show source types and system versions in the library. Then open **Chunk explorer** using the sidebar. The library is the document inventory; the explorer shows the searchable passages made from one selected document.

## 3. Chunk explorer: code, SQL, and long prose (2 minutes)

Nothing needs to be pasted for this section. These three sources are in the baseline. Move the slider and release it to refresh the preview. A preview alone does not change retrieval.

### A. Python: preserve symbol boundaries

**DO:** In **Document to inspect**, choose the legacy **Business Rules** document ending in `blpts_legacy/code/business_rules.py`. Set the limit to **1,800**.

> **SAY:** For Python, the parser understands where classes and functions start and end. Here, the file description is one chunk and the fee function is another. The function name and line numbers tell us where the code came from.

**SHOW:** **Boundary strategy: Python symbols**. Open **Full chunk text & metadata** and select the second chunk. Point to `business_rules.calculate_renewal_fee_db_side`, its function kind, and its source lines. At 1,800 characters this sample has two chunks: module information and the complete function.

**DO:** Change to **400**, then back to **1,800**.

> **SAY:** If I lower the limit, this function has to split. If I raise it again, the whole function fits. Separate functions still stay separate.

### B. SQL: pack complete statements together

**DO:** Choose the legacy **Seed Data** document ending in `blpts_legacy/code/db/seed_data.sql`. Set the limit to **500**, then **1,800**.

> **SAY:** SQL is handled differently. We keep whole statements together where they fit. Watch what happens when I raise the limit. More statements fit in each chunk, so we get fewer chunks.

**SHOW:** **SQL statements**. For this fixture, expect **7 chunks at 500** and **2 at 1,800**. Open a full chunk to show multiple `INSERT` statements. The card is only a short preview, so use the full-text expander to show all the statements. SQL Server `GO` batch boundaries remain separate. A statement larger than the limit still requires splitting.

### C. Prose: headings and paragraphs in a long document

**DO:** Choose **BLPTS discovery and handover handbook**. Its file is `blpts_legacy/documents/discovery_and_handover_handbook.md`. Set the limit to **400**, then **1,800**. Scroll through the chunk cards and inspect a chunk from **Review document structure before indexing**.

> **SAY:** This is a long document about discovery and handover. Here, we use headings and paragraphs. A larger limit lets more paragraphs from the same section fit together. The heading and line numbers tell us where each chunk came from.

**SHOW:** **Headings / paragraphs**, the heading labels, line ranges, and the source highlighting. The section about reviewing document structure contains several paragraphs, making the difference easy to see. The handbook describes a proposed discovery process; it does not supply missing application settings or resolve the demo's historical conflicts.

**DO:** Return the slider to **1,800**. If **Apply chunk size & rebuild index** is enabled, click it. If it is disabled, the live index already matches. Use the default limit for the Q&A sequence so you are changing the evidence rather than the chunking configuration between answers.

> **SAY:** When we ask a question, the app finds relevant chunks and sends the parts that fit to the model. It doesn't send every document for every question.

## 4. Live Q&A: find the missing AMI requirements

> **SAY:** Let's say I'm a PM gathering requirements for the AMI retry feature. AMI stands for Advanced Metering Infrastructure. In this example, meters send data to the system. If an upload fails, the system tries again.
>
> I need to know how many times it tries, how long it waits between attempts, and what happens if they all fail.
>
> I'll ask the same question with Modernized only, Legacy only, and Compare both so we can see what information each has.

**DO:** Open **Live Q&A** and paste this into **Your question**:

```text
What are the exact AMI meter retry limits and backoff timings?
```

### A. Modernized only: no AMI information yet

**DO:** Choose **Modernized only**, then click **Generate answer**.

> **SAY:** There's no AMI retry information in the modernized sources yet. For this example, the team hasn't built that feature yet.

Show the absence of relevant evidence or the answer’s information-gap message. Do not treat a lack of modernized evidence as proof that the feature has no requirement.

### B. Legacy only: basic information, but no exact settings

**DO:** Change **Source scope** to **Legacy only**, click **Generate answer**, open **Cited evidence** or **Retrieved sources**, then click **Pin baseline**.

> **SAY:** The legacy documents tell us it retries and waits longer between attempts. But they don't say how many times or how long it waits. Those are the details I need to ask the client about.

**Expected evidence:** **Retry handling** from `MeterDataIntegration.md` describes exponential backoff without exact settings. **Retry discussion** records the documentation gap. Explain that the sources do not establish the exact values. If the generated answer supplies unsupported numbers, call out the mismatch; do not present them as confirmed.

### C. Compare both systems: check what each version has

**DO:** Change **Source scope** to **Compare both systems** and click **Generate answer**. Briefly show the version labels and retrieval details, then switch back to **Legacy only**.

> **SAY:** Here we can check both versions. The legacy side has some basic information, and the modernized side has none for this feature yet. We still need the client to confirm the settings.

## 5. Client clarification: add the response as legacy evidence

> **SAY:** As the PM, I ask the client how many retries there are and how long the system waits. A few days later, they reply by email with the settings.
>
> I'll add that response here, tag it as Legacy, and publish it.

**DO:** Open **Knowledge base → Add document**. Paste this into **New document title**:

```text
AMI retry configuration: owner clarification
```

Set **New source version** to **Legacy**, **Source type** to **Document**, and **Effective from** to **2026-09-29**. We are recording the response as a standalone clarification document; Email is also available for importing the original correspondence.

Paste the complete block into **New source content**:

```markdown
# AMI retry configuration: owner clarification

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

> **SAY:** It's saved now. We can see the new revision and who added it. In this demo, that name is Sparsha.

## 6. Live Q&A: ask again after adding the response

> **SAY:** A few weeks later, someone else joins the team and asks the same question. They weren't on that email thread.
>
> I'll ask again. This time the client response is available, so we can get the settings and open the source they came from.

**DO:** Return to **Live Q&A**, keep **Legacy only**, and generate the same question again:

```text
What are the exact AMI meter retry limits and backoff timings?
```

Open **Before & after**, then inspect the new citation. The evidence supports **4 retries**, with delays of **5, 10, 20, and 40 seconds**, followed by the dead-letter queue and an operations alert.

Show **Retrieval details** and click a circled **?** beside a score or parameter. Explain that relevance scores are search scores, not confidence percentages. Retrieved passages and passages sent to the model may differ because of the request-size budget.

## 7. Client correction: edit the existing document

> **SAY:** Now the client comes back with a correction. A firmware update added a fifth retry. I'll open the same document and update it.
>
> We can see who changed it, the date it applies from, and the earlier version in the history.

**DO:** Pin the four-retry answer as the new baseline. Open **Knowledge base → Document library**. Select the current **AMI retry configuration: owner clarification** source. Keep the title, **Legacy** version, and **Document** type. Set **Effective from** to **2026-09-30**.

Replace the entire **Source content** with this block:

```markdown
# AMI retry configuration: owner clarification

Integration Operations | 2026-09-30

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

> **SAY:** The new answer uses five retries. We can still open the earlier revision to see the four-retry guidance it replaced.

## 8. Implement the requirement in the modernized application

> **SAY:** Let's move forward in the project. The team has now built this feature in .NET using the confirmed settings. We should add the new code to the knowledge base too. I'll use this sample to show that step.

**DO:** Open **Knowledge base → Add document**. Use **Modernized** for **New source version**, **Code** for **Source type**, and **2026-10-01** for **Effective from**.

Paste this into **New document title**:

```text
AmiRetryPolicy.cs
```

Paste this into **New source content**:

```csharp
// Synthetic modernized AMI retry policy, effective 2026-10-01.
// Preserves the corrected legacy owner clarification dated 2026-09-30.
// Five retries after the initial failed upload: 5, 10, 20, 40, 80 seconds.
namespace Modernized.Ami;

public static class AmiRetryPolicy
{
    public const int MaxRetryAttempts = 5;
    public static int[] RetryDelaysSeconds => new[] { 5, 10, 20, 40, 80 };
    public const string FailedUploadDestination = "ami-dead-letter-queue";
    public const bool RaiseOperationsAlertAfterFinalFailure = true;
    public const bool PreserveOriginalUploadIdentifierOnReplay = true;
}
```

Review **Chunk preview**, then click **Publish to knowledge base**.

Presenter note: this sample represents a future completed implementation for the story. Publishing code adds searchable evidence; it does not implement or deploy an AMI service. C# currently uses the safe text chunker, not the Python AST parser.

> **SAY:** I'll tag this as Modernized and Code. We now have the client's legacy guidance and a sample of the code that uses those settings in the new application.

**DO:** Return to **Live Q&A**, select **Modernized only**, and generate the original question again:

```text
What are the exact AMI meter retry limits and backoff timings?
```

> **SAY:** At the start, Modernized only had no answer for this question. Now it has the code with five retries and the delay values. Let's open that source.

**DO:** Now select **Compare both systems**, and paste:

```text
What AMI retry policy does the modernized implementation use, and which current legacy requirement does it preserve?
```

Generate the answer. Show one legacy citation and the new modernized code citation.

> **SAY:** Now we can compare both. The client confirmed five retries, with waits of 5, 10, 20, 40, and 80 seconds. We can see those same settings in the modernized code.

## Closing: coming full circle

> **SAY:**
> That brings us full circle. The next person can find the requirement, see what changed, and check how it was implemented. That's what we mean by Continuity.

## Reset after the presentation

Use **Knowledge base → Reset & activity → Restore baseline corpus** when ready to discard the demo edits. This restores the original corpus, including the long handbook, and the default chunk size. Older answers may remain visible in history with their original revision; generate a new baseline answer for the next presentation.

If you want to keep the session's documents first, use **Export workspace documents**. The export is an archival snapshot, not an automatic restore format. The in-session author tag is the demo identity, not proof of authenticated user attribution.
