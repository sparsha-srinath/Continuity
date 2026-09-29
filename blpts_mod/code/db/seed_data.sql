INSERT INTO staff VALUES (1, 'R. Colston', 'Clerk Supervisor', '2010-04-01', NULL, 'active');
INSERT INTO staff VALUES (2, 'J. Pae', 'IT Support', '2019-06-01', NULL, 'active');
INSERT INTO staff VALUES (3, 'M. Alvarez', 'Licensing Clerk', '2017-08-15', NULL, 'active');
INSERT INTO staff VALUES (4, 'K. Ibarra', 'Applications Developer', '2025-11-03', NULL, 'active');

INSERT INTO ordinances VALUES (1, 2011, 'Ordinance 2011-07', '15% fee increase for license types A and B, effective 2011.', 'A,B', 'yes');
INSERT INTO ordinances VALUES (2, 2016, 'Ordinance 2016-03', 'Establishes Home Occupation Plus designation for type C.', 'C', 'yes');
INSERT INTO ordinances VALUES (3, 2009, 'Ordinance 2009-14, Section 3(b)', 'Exempts low-risk business categories (C, E) from mandatory 30-day inspection scheduling. Confirmed via County Clerk correspondence, 2026-03-11.', 'C,E', 'yes');

INSERT INTO licenses VALUES (1, 'Riverside Hardware', 'A', '2005-03-10', 'active');
INSERT INTO licenses VALUES (2, 'Main Street Diner', 'B', '2006-07-22', 'active');
INSERT INTO licenses VALUES (3, 'Alvarez Home Bakery', 'C', '2015-02-01', 'active');
INSERT INTO licenses VALUES (4, 'Chen Tutoring Services', 'C', '2017-05-19', 'active');
INSERT INTO licenses VALUES (5, 'Countywide Electric Contracting', 'D', '2008-09-14', 'active');
INSERT INTO licenses VALUES (6, 'Helping Hands Food Pantry', 'E', '2012-11-30', 'active');

-- Post-go-live renewals, unified calculation, no drift
INSERT INTO license_renewals VALUES (1, 3, 2026, 1, 75.00, 0.00, 3);
INSERT INTO license_renewals VALUES (2, 4, 2026, 1, 75.00, 0.00, 3);
-- Multi-year renewal example, new feature
INSERT INTO license_renewals VALUES (3, 1, 2026, 3, 465.19, 51.69, 3);

INSERT INTO inspections VALUES (1, 3, '2026-02-10', '2026-02-15', 1, 'Ordinance 2009-14, Section 3(b)');
INSERT INTO inspections VALUES (2, 4, '2026-02-12', NULL, 1, 'Ordinance 2009-14, Section 3(b)');
