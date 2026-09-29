# Presenting Continuity

From the `demo` branch, run `./run_demo.ps1 -Install` for first-time setup
(Python 3.11+). After dependencies are installed, use `./run_demo.ps1`.
The demo opens at http://127.0.0.1:8502/?demo=1. Use `-Port 8503` if needed.
On other platforms, install `requirements.txt`, then run
`python -m streamlit run app.py -- --demo`.

You can also enable **Guided demo** in the normal app or open `/?demo=1`.
Once dependencies are installed, the prepared walkthrough needs no model,
API key, or network service. It reads the checked-in synthetic corpus without
initializing Chroma or writing query metadata. Live Q&A retains its existing
provider and storage configuration.

## Five-minute walkthrough

1. **Renewal fee conflict:** explain the $50/$75 discrepancy, then open the
   legacy screen and modernized calculation sources. The comparison connects
   a discovered defect to the code that resolves it.
2. **Inspection rationale:** show the clerk's correspondence and preserved
   C/E exemption. Distinguish the correspondence from the ordinance scan,
   which is not included in the export.
3. **Stale surcharge documentation:** compare the policy, ticket, and code.
   The records show drift but do not settle which rule is currently approved.
4. **Knowledge gap:** show that the AMI records cannot supply exact retry
   limits or timings. Explain what evidence the team would need next.

Use **Next scenario**, **Previous**, or the scenario selector to navigate.
**Restart demo** returns to the first scenario. Source links open a separate
tab and highlight the selected passage within the available local document.
For synthetic records without a standalone file, the viewer shows the indexed
record and labels that limitation.

The prepared summaries and source selections are presentation content, not
model-generated answers or a demonstration of live retrieval quality. This is
labeled in the UI. **Ask live model** submits the current question with its
scenario scope through the normal retrieval, generation, and citation validation
pipeline. Configure a provider first using the main README; without one, the
app reports the configuration issue and exposes retrieved sources. There is no
silent fallback from a failed live answer to a prepared summary.

Prepared scenarios check their required source passages at runtime and report
an error when a referenced passage is unavailable. After editing the corpus,
review the prepared summaries and run `python -m pytest -q` before presenting.
