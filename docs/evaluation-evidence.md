# Evaluation Evidence

## Summary

The repository contains automated tests that verify retrieval behavior,
citation handling, context budgeting, session isolation, safe index updates,
and key Streamlit workflows. This is implementation-level verification, not a
formal RAG evaluation report.

No checked-in benchmark dataset, relevance labels, ground-truth answers,
retrieval-quality metrics, groundedness scores, or model-comparison results
were found in the repository.

## Verified Automated Coverage

| Area                                    | Evidence                                                                 | What the tests establish                                                                                                                                                      |
| --------------------------------------- | ------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Retrieval and version comparison        | `tests/test_blpts_modernization.py`                                      | Expected legacy and modernized passages are selected; compare mode retains both versions; version-scoped requests do not leak modernized records into legacy context.         |
| Context budgeting and source fidelity   | `tests/test_blpts_modernization.py`                                      | Prompts remain within the configured byte budget; selected excerpts remain exact source substrings; Unicode source text is handled within the same budget.                    |
| Citation validation                     | `tests/test_blpts_modernization.py`                                      | Citation references must identify passages sent in the model context; invalid references and malformed responses fail closed; compare answers require both available systems. |
| Retrieval failure behavior              | `tests/test_blpts_modernization.py`, `tests/test_knowledge_assistant.py` | The model is not called when no relevant evidence is retrieved; missing model configuration remains distinct from missing evidence.                                           |
| Session isolation and mutation behavior | `tests/test_demo.py`                                                     | Browser-session workspaces have independent indexes; add, edit, remove, clear, restore, and rebuild operations update the active index safely.                                |
| Atomic index replacement                | `tests/test_demo.py`                                                     | A failed rebuild retains the previous collection and revision.                                                                                                                |
| Import safety and retrieval             | `tests/test_codebase_import.py`                                          | Imported code is validated before indexing and can be retrieved after a successful import.                                                                                    |
| UI workflows and observability          | `tests/test_app.py`                                                      | The Streamlit UI supports evidence publishing, reindexing, answer pinning/comparison, and source visibility after model failure.                                              |

## What This Does Not Prove

The automated tests do not measure production retrieval or answer quality.
They do not establish:

- Recall@k, precision@k, MRR, or nDCG for retrieval.
- Whether a representative user question retrieves all required evidence.
- Claim-to-source entailment or answer groundedness beyond citation membership.
- Comparative quality, latency, or structured-output reliability across Qwen,
  Gemma, OpenAI, Anthropic, or other models.
- Quality under production data volume, concurrent users, or live connectors.

Citation membership is checked: a cited reference must come from the evidence
sent to the model. This is not an entailment check; a citation alone does not
prove that every answer claim is supported by that passage.

## Reproducible Automated Check

Run the test suite from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp .\.pytest-evaluation-tmp
```

Most recent verified execution: **51 passed in 13.73 seconds** on 2026-10-05.

Remove the generated temporary directory after the run:

```powershell
Remove-Item -Recurse -Force .\.pytest-evaluation-tmp
```

## Recommended Formal Evaluation

To convert this coverage into an evaluation report, add a versioned dataset of
representative questions with expected source IDs, accepted answer facts, and
expected version scope. Report retrieval metrics such as Recall@8 and MRR, then
evaluate answer groundedness with claim-to-source review. Run the same dataset
across configured models and record structured-output validity, citation
validity, groundedness, latency, and failure rate.
