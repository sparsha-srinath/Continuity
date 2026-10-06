# BLPTS discovery and handover handbook

Document owner: Sparsha
Date: 2026-10-05
Classification: Synthetic demonstration guidance

This handbook is a deliberately long document for demonstrating how Continuity separates prose into sections and paragraphs. It describes a proposed discovery and handover process for the fictional Business License & Permit Tracking System (BLPTS). It is not a historical ordinance, a client approval, or evidence of a production system's behavior. Use the original code, records, correspondence, and confirmed decisions when answering questions about specific business rules.

The handbook accompanies the legacy and modernized demonstration applications. Its purpose is to explain how a team can gather and maintain knowledge during modernization, from the first walkthrough to operational handover. The application examples contain invented records and intentional knowledge gaps. Guidance in this document should help participants organize their investigation without filling those gaps with assumptions.

## 1. Establish the discovery scope

Begin by agreeing which workflows the demonstration covers. BLPTS includes license records, renewal processing, fee calculation, and inspection scheduling. A single screen rarely represents the full workflow: the visible action may depend on database records, background processing, shared modules, or decisions that were never written down. Record the workflow name and the role performing it before collecting implementation details.

Write a short scope statement for each investigation. Identify the user action being examined, the application version, the expected output, and the evidence currently available. Avoid a scope statement such as "understand everything about licensing." A more useful statement is "trace the selected renewal from the clerk's screen to the calculation that supplies its displayed total." That statement can be tested and handed to another person.

Keep discovery findings separate from proposed improvements. A participant may suggest a better approval process during a walkthrough, but that suggestion does not establish how the existing application behaves. Label observations, hypotheses, proposed changes, and approved decisions explicitly. A future reader should be able to tell whether a note describes something seen on screen or an idea that still needs review.

## 2. Prepare the application walkthrough

Before the meeting, prepare a synthetic record that can be used in both application previews. Note the record's identifier and the fields that will be inspected. Choose a demonstration path that does not require real personal information or a production connection. The goal is to understand the sequence of operations, not to demonstrate access to sensitive records.

Ask the operator to explain their normal sequence without skipping familiar steps. Experienced staff often omit a manual check because it feels obvious to them. Capture those checks in ordinary language: which value they compare, where they look for supporting information, and what causes them to stop or ask for help. These observations can reveal dependencies that do not appear in source code.

After the walkthrough, replay the sequence using the same synthetic input. Confirm that the team can locate the relevant screen, identify the source of the displayed information, and describe the outcome. If the replay differs, record the difference rather than silently editing the notes to make both observations agree. Reproducibility is more useful than a polished but incomplete description.

## 3. Build an inventory of evidence

Create an inventory that includes source code, SQL definitions, sample data, operating notes, correspondence, and work items. For every item, record its location, the version it describes, the source type, and a short description of its purpose. A filename alone is often insufficient: a file named rules.py may contain only one part of the workflow, while an email may explain why another path behaves differently.

Preserve the original wording and formatting where practical. Code indentation, document headings, and paragraph breaks provide useful structure for both readers and the chunking process. A screenshot can establish what was displayed, but it does not replace searchable source text. When transcribing a screenshot or meeting note, label the transcription and keep a reference to the original artifact.

Do not treat every collected item as equally authoritative. A released implementation, a draft note, and an unconfirmed recollection have different roles in an investigation. Record enough provenance for reviewers to make that distinction. The assistant can retrieve an item because its wording matches a question; that match alone does not establish that the item is approved or current.

## 4. Trace a screen action into implementation

Start with the action the user performs and follow the implementation in order. Identify the event handler, any shared calculation function, and the query or record used to supply inputs. Note when the same workflow can be entered from another screen. Different entry points may contain separate logic even when their labels look identical to an operator.

For a Python artifact, record the module and qualified function name rather than copying a few lines without context. The function signature identifies the inputs, the body shows the implemented branches, and nearby comments may explain assumptions. Distinguish executable behavior from comments: a comment can describe intended behavior while the implementation does something else.

For SQL artifacts, distinguish table definitions, constraints, reference data, and historical transactions. A row in sample data demonstrates a stored value; it does not by itself establish which calculation produced that value. Connect the record to the workflow and implementation using identifiers or documented relationships. If that connection is missing, leave it as an investigation question.

## 5. Record conflicts without resolving them prematurely

When two sources disagree, preserve both and state the disagreement precisely. Identify the input or condition under which the results diverge, the source responsible for each result, and the dates or versions involved. Avoid a broad statement such as "the old system is inconsistent" when a smaller statement can identify the conflicting paths and the evidence needed to decide between them.

Create a focused clarification request. Include the competing explanations, links to their sources, the consequence for modernization, and the person or group expected to respond. Ask for the intended rule and its scope, not simply which document should be deleted. A conflict can reflect a legitimate historical change, different operating conditions, or a defect that was tolerated for years.

After an answer arrives, record what was confirmed and what remains unresolved. Preserve the earlier evidence as history when it explains prior behavior. A later decision may define the target implementation without proving that every earlier transaction was wrong. Reviewers should be able to follow the reasoning from the original disagreement to the approved interpretation.

## 6. Write useful clarification requests

A useful request contains one principal question, enough background to understand it, and a clear description of the decision it enables. Include the system version and workflow being discussed. If the question asks for exact operational settings, list the missing parameters explicitly, but do not suggest invented values merely to make the request look complete.

Assign a responsible person and record when the request was sent. If the recipient forwards it to another team, keep that handoff with the request so the eventual answer has a traceable source. A project manager can coordinate the exchange, but technical and operational reviewers should confirm that the reply addresses the original question rather than a similar workflow.

When the response is received, separate the answer from the email's unrelated discussion. Preserve enough context to show who supplied the information and what it applies to. A short standalone clarification can be easier to retrieve than a long thread, provided its title, effective date, source reference, and limitations remain attached to the content.

## 7. Capture decisions with scope and dates

Each decision record should explain the question, the chosen interpretation, the supporting evidence, and the boundary of the decision. For example, a decision about a modernized workflow should not automatically be applied to historical behavior. State whether the decision describes the existing application, the target application, or a migration procedure between them.

Use an effective date to distinguish when guidance applies from when somebody entered it into the workspace. Those dates can differ. A later meeting may confirm a rule that was already in effect, or approve a change that takes effect in the future. Keep the source's own dates visible and avoid replacing them with a generic "last updated" label that loses the distinction.

Record the person making the update and identify any earlier guidance it replaces. Corrections should create a new revision with a clear relationship to the previous one. Readers examining an older answer should still be able to understand which information was available at the time, while new investigations should use the current guidance where the application supports that distinction.

## 8. Prepare representative validation examples

Build a small set of examples that exercise the workflow's meaningful branches. Include ordinary inputs, boundary conditions, and cases mentioned in support records. Use synthetic records and explain why each example is included. The purpose is not to accumulate a large spreadsheet of repetitive cases but to make each decision branch visible to reviewers.

Record expected outcomes only when they have a supporting source or an explicit approved decision. If an outcome is unknown, label the example as an open question. Running an old implementation can reveal its output, but that output alone does not prove the intended business rule. Keep observed results and approved expectations in separate fields.

When comparing the two versions, use matching inputs and document intentional differences. A new feature can be valid even though no legacy equivalent exists. Conversely, a similar-looking result can hide different assumptions. The comparison should explain what is preserved, what changes, and which evidence supports the distinction without rewriting the history of the original application.

## 9. Review document structure before indexing

Use descriptive headings that name the subject of the section. A heading such as "Handling unresolved decisions" gives readers more information than "Other notes." Keep paragraphs focused on a single idea and separate a new topic with a heading rather than adding it to an unrelated section. This makes the document easier to review and gives the prose chunker meaningful boundaries.

Keep explanations and their necessary qualifications close together. If a paragraph describes an action that applies only to a particular workflow, state that restriction in the same paragraph or immediately next to it. Retrieval may select one passage from a large document, so relying on a caveat many pages away can leave a selected passage ambiguous. Clear writing improves the usefulness of a retrieved excerpt without guaranteeing that the generated answer is correct.

Use the Chunk explorer to inspect the resulting passages. The maximum character setting is a limit rather than a request to fill every chunk exactly. Paragraphs under the same heading can share a chunk if they fit; a new heading begins a separate section. A section that is longer than the selected limit may require several passages. Examine the heading and source line range to see where each passage belongs.

For a larger document, compare a small character limit with the default. At a small limit, an explanation may span several passages. At a larger limit, neighboring paragraphs within the same section may fit together. The document should remain reconstructable from the ordered passages without rewritten wording or overlapping text. Changes to a preview do not alter the search index until the presenter applies the rebuild.

Remember that indexing and request context are different stages. Indexing creates searchable passages for the whole corpus. When a question arrives, retrieval ranks relevant passages and the context packer selects excerpts that fit the model request. A complete indexed section can still be shortened when preparing a request. Inspect the evidence sent to the model when explaining an answer, rather than assuming the model received every chunk from the document.

## 10. Organize review meetings around evidence

Send reviewers a short agenda containing the decisions that need attention and links to the relevant sources. Avoid a meeting that starts by searching every shared folder while participants wait. The inventory should make it possible to open the implementation, supporting note, and unresolved question quickly enough to spend the meeting discussing their meaning.

During the meeting, distinguish a confirmed answer from a follow-up action. If a participant says they need to check an archive, record that as an action with an owner rather than a resolved decision. If the team agrees on a target behavior, record whether it also explains historical behavior. Those are different claims and may require different evidence.

After the meeting, publish a concise update with the decisions and outstanding items. Link the update to the questions it addresses so a future team member does not have to reconstruct the entire conversation. Ask the relevant reviewer to verify the wording, especially where a small qualification changes the scope of the decision. The published record should be understandable without access to the meeting itself.

## 11. Plan the operational handover

Prepare handover material around the tasks the receiving team must perform. Explain how to locate a record, investigate a reported discrepancy, identify the relevant system version, and find the current supporting decision. Include known limitations and open questions. A handover that describes only the happy path leaves the next team without a method for dealing with uncertainty.

Organize references by workflow and responsibility. The support team may need a different entry point from a developer reviewing a calculation, but both should reach the same underlying evidence. Prefer references to maintained source records over independent copies that can drift apart. If a copy is necessary, record its date and relationship to the source so readers know when to verify it.

Schedule a practical handover exercise using synthetic records. Ask a person who did not write the notes to follow them and explain the result. Observe where they need extra context, encounter an ambiguous label, or cannot find a referenced artifact. Improve those areas before declaring the handover complete. Successful knowledge transfer means another person can use the material, not merely that a document exists.

## 12. Maintain the knowledge after the demonstration

Treat the knowledge base as a maintained project artifact. When a new clarification arrives, identify the existing question or document it affects, record the source and date, and publish a revision when appropriate. Avoid adding duplicate documents with competing values simply because publishing a new item is easier than locating the existing one.

Revisit unresolved questions at agreed project checkpoints. Some may become answerable as additional records are found, while others may require a deliberate target-state decision because historical evidence cannot be recovered. Preserve that distinction. Choosing how the replacement should behave is a valid project action, but it should not be presented as proof of what the original designers intended.

For this demonstration, the browser workspace is temporary and isolated. Restoring the baseline recreates the repository's sample documents; it does not represent durable production storage or a permanent audit system. Explain the revision history as a demonstration of provenance within the session. A production rollout needs an agreed retention, identity, and governance design before it can be relied on as the organization's lasting record.
