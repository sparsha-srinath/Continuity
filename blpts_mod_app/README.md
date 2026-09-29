# BLPTS Modernized App

Phase 2 is an additive modernized replacement for the fictional legacy BLPTS PowerBuilder/Sybase stand-in. It keeps its SQLite database separate from `blpts_dummy_app`.

The fee calculation is unified and always applies the type-C Home Occupation Plus surcharge. The inspection exemption is explicitly tied to Ordinance 2009-14, Section 3(b). The multi-year renewal discount is intentionally new and has no legacy equivalent; it exists to test version-scoped retrieval.

## Run

```powershell
sqlite3 db/blpts_mod.db < db/schema.sql
sqlite3 db/blpts_mod.db < db/seed_data.sql
python app/demo_mod_features.py
```

The knowledge assistant indexes these modernized artifacts with `system_version = mod_v1`, while legacy artifacts remain tagged `legacy`.

## Web UI

From the repository root, start the static UI with:

```powershell
Push-Location blpts_mod_app
python -m http.server 8766
```

Then open `http://localhost:8766/ui/`. The Bootstrap interface includes dashboard navigation, license records, the unified renewal calculator, multi-year discounts, and the confirmed inspection-rule source.
