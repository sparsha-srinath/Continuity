# BLPTS Dummy Legacy App

This is a fictional stand-in for a legacy County Business License & Permit Tracking System (BLPTS), originally imagined as a PowerBuilder 9 / Sybase SQL Anywhere application. It is implemented in Python, SQLite, and static HTML because no PowerBuilder runtime is available in the target environment.

The fee calculation mismatch between `app/business_rules.py` and `app/screen_license_renewal.py` is intentional demo material and must not be fixed. The inspection exemption ambiguity in `app/inspection_scheduler.py` is also intentional and must not be resolved with a made-up explanation.

## Run the demo

From this directory:

```powershell
sqlite3 db/blpts.db < db/schema.sql
sqlite3 db/blpts.db < db/seed_data.sql
python app/demo_fee_conflict.py
```

If the `sqlite3` command-line tool is unavailable, the Python demo can still show the code-level mismatch; the historical database section requires the generated database file.

## View the UI prop

Open `ui/blpts_renewal_screen.html` directly in a browser. It is self-contained, uses no server, build step, backend calls, or external assets.

The static UI includes separate navigation paths for Regular Clerk and Administrator roles. Clerks can use the dashboard, renewal, license, and inspection pages. Administrators can also maintain staff and fee schedule records. The maintenance pages contain dummy CRUD data, required-field validation, duplicate-key validation, and retro modal message boxes for access and data errors. Use the role selector in the toolbar to preview both permission paths.

## Scope

The `.zip` files in `legacy_artifacts/` are empty placeholders representing chaotic legacy version control. This fixture deliberately preserves conflicting business logic and undocumented history for use in a RAG assistant demonstration.
