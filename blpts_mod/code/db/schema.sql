-- BLPTS Modernized schema.
-- Same core tables as legacy, with calculated_by removed (single
-- calculation path now) and multi-year renewal fields added.

CREATE TABLE staff (
    staff_id        INTEGER PRIMARY KEY,
    name            TEXT NOT NULL,
    role            TEXT,
    start_date      TEXT,
    end_date        TEXT,
    status          TEXT
);

CREATE TABLE ordinances (
    ordinance_id    INTEGER PRIMARY KEY,
    year            INTEGER NOT NULL,
    title           TEXT,
    description     TEXT,
    affects_license_type TEXT,
    full_text_on_file TEXT
);

CREATE TABLE licenses (
    license_id      INTEGER PRIMARY KEY,
    business_name   TEXT NOT NULL,
    license_type    TEXT NOT NULL,
    issue_date      TEXT,
    status          TEXT
);

CREATE TABLE license_renewals (
    renewal_id      INTEGER PRIMARY KEY,
    license_id      INTEGER NOT NULL,
    renewal_year    INTEGER NOT NULL,
    renewal_term_years INTEGER NOT NULL DEFAULT 1,
    fee_charged     REAL NOT NULL,
    discount_applied REAL NOT NULL DEFAULT 0.00,
    processed_by    INTEGER,
    FOREIGN KEY (license_id) REFERENCES licenses(license_id)
);

CREATE TABLE inspections (
    inspection_id   INTEGER PRIMARY KEY,
    license_id      INTEGER NOT NULL,
    scheduled_date  TEXT,
    completed_date  TEXT,
    exempt_flag     INTEGER,
    exempt_reason   TEXT,
    FOREIGN KEY (license_id) REFERENCES licenses(license_id)
);
