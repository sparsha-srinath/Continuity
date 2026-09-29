-- BLPTS (Business License & Permit Tracking System)
-- Original schema authored 2003 for Sybase SQL Anywhere.
-- Recreated here in SQLite for prototyping only -- table/column
-- structure mirrors the original as closely as practical.

CREATE TABLE staff (
    staff_id        INTEGER PRIMARY KEY,
    name            TEXT NOT NULL,
    role            TEXT,
    start_date      TEXT,
    end_date        TEXT,           -- NULL if still active
    status          TEXT            -- 'active', 'departed', 'contractor_ended'
);

CREATE TABLE ordinances (
    ordinance_id    INTEGER PRIMARY KEY,
    year            INTEGER NOT NULL,
    title           TEXT,
    description     TEXT,
    affects_license_type TEXT,      -- FK-ish, not enforced (as in the original)
    full_text_on_file TEXT          -- 'yes' / 'no' / 'partial' -- many county ordinances predate digitization
);

CREATE TABLE fee_schedule (
    fee_schedule_id INTEGER PRIMARY KEY,
    license_type    TEXT NOT NULL,
    base_fee        REAL NOT NULL,
    effective_year  INTEGER NOT NULL,
    entered_by      INTEGER,        -- FK to staff
    notes           TEXT
);

CREATE TABLE licenses (
    license_id      INTEGER PRIMARY KEY,
    business_name   TEXT NOT NULL,
    license_type    TEXT NOT NULL,  -- 'A' Retail, 'B' Food Service, 'C' Home Occupation, 'D' Contractor, 'E' Non-Profit
    issue_date      TEXT,
    status          TEXT
);

CREATE TABLE license_renewals (
    renewal_id      INTEGER PRIMARY KEY,
    license_id      INTEGER NOT NULL,
    renewal_year    INTEGER NOT NULL,
    fee_charged     REAL NOT NULL,
    calculated_by   TEXT,           -- 'db_side' or 'screen_side' -- which code path computed this
    processed_by    INTEGER,        -- FK to staff
    FOREIGN KEY (license_id) REFERENCES licenses(license_id)
);

CREATE TABLE inspections (
    inspection_id   INTEGER PRIMARY KEY,
    license_id      INTEGER NOT NULL,
    scheduled_date  TEXT,
    completed_date  TEXT,
    exempt_flag     INTEGER,        -- 1 = exempt from 30-day rule, 0 = not
    exempt_reason   TEXT,
    FOREIGN KEY (license_id) REFERENCES licenses(license_id)
);
