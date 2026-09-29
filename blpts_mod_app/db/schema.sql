CREATE TABLE staff (staff_id INTEGER PRIMARY KEY, name TEXT NOT NULL, role TEXT, start_date TEXT, end_date TEXT, status TEXT);
CREATE TABLE ordinances (ordinance_id INTEGER PRIMARY KEY, year INTEGER NOT NULL, title TEXT, description TEXT, affects_license_type TEXT, full_text_on_file TEXT);
CREATE TABLE fee_schedule (fee_schedule_id INTEGER PRIMARY KEY, license_type TEXT NOT NULL, base_fee REAL NOT NULL, effective_year INTEGER NOT NULL, entered_by INTEGER, notes TEXT);
CREATE TABLE licenses (license_id INTEGER PRIMARY KEY, business_name TEXT NOT NULL, license_type TEXT NOT NULL, issue_date TEXT, status TEXT);
CREATE TABLE license_renewals (renewal_id INTEGER PRIMARY KEY, license_id INTEGER NOT NULL, renewal_year INTEGER NOT NULL, fee_charged REAL NOT NULL, processed_by INTEGER, renewal_term_years INTEGER NOT NULL DEFAULT 1, discount_applied REAL NOT NULL DEFAULT 0.00, FOREIGN KEY (license_id) REFERENCES licenses(license_id));
CREATE TABLE inspections (inspection_id INTEGER PRIMARY KEY, license_id INTEGER NOT NULL, scheduled_date TEXT, completed_date TEXT, exempt_flag INTEGER, exempt_reason TEXT, FOREIGN KEY (license_id) REFERENCES licenses(license_id));
