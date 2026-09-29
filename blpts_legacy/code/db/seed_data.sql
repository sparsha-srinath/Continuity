-- Staff
INSERT INTO staff VALUES (1, 'T. Whitfield', 'Original Developer', '2003-01-15', '2015-12-31', 'contractor_ended');
INSERT INTO staff VALUES (2, 'D. Marsh', 'Applications Developer', '2016-02-01', '2020-11-30', 'departed');
INSERT INTO staff VALUES (3, 'R. Colston', 'Clerk Supervisor', '2010-04-01', NULL, 'active');
INSERT INTO staff VALUES (4, 'J. Pae', 'IT Support', '2019-06-01', NULL, 'active');
INSERT INTO staff VALUES (5, 'M. Alvarez', 'Licensing Clerk', '2017-08-15', NULL, 'active');

-- Ordinances
INSERT INTO ordinances VALUES (1, 2011, 'Ordinance 2011-07', '15% fee increase for license types A and B, effective 2011.', 'A,B', 'partial');
INSERT INTO ordinances VALUES (2, 2016, 'Ordinance 2016-03', 'Establishes Home Occupation Plus designation for type C.', 'C', 'yes');
INSERT INTO ordinances VALUES (3, 2009, 'Ordinance 2009-14', 'Possible source of inspection exemption for low-risk categories; unconfirmed.', 'C,E', 'no');

-- Fee schedule
INSERT INTO fee_schedule VALUES (1, 'A', 150.00, 2003, 1, 'Original base fee.');
INSERT INTO fee_schedule VALUES (2, 'B', 200.00, 2003, 1, 'Original base fee.');
INSERT INTO fee_schedule VALUES (3, 'C', 50.00, 2003, 1, 'Original base fee.');
INSERT INTO fee_schedule VALUES (4, 'D', 175.00, 2003, 1, 'Original base fee.');
INSERT INTO fee_schedule VALUES (5, 'E', 0.00, 2003, 1, 'Non-profit, exempt from base fee.');

-- Licenses
INSERT INTO licenses VALUES (1, 'Riverside Hardware', 'A', '2005-03-10', 'active');
INSERT INTO licenses VALUES (2, 'Main Street Diner', 'B', '2006-07-22', 'active');
INSERT INTO licenses VALUES (3, 'Alvarez Home Bakery', 'C', '2015-02-01', 'active');
INSERT INTO licenses VALUES (4, 'Chen Tutoring Services', 'C', '2017-05-19', 'active');
INSERT INTO licenses VALUES (5, 'Countywide Electric Contracting', 'D', '2008-09-14', 'active');
INSERT INTO licenses VALUES (6, 'Helping Hands Food Pantry', 'E', '2012-11-30', 'active');

-- License renewals -- includes the planted historical conflict for type C in 2019
INSERT INTO license_renewals VALUES (1, 1, 2019, 172.50, 'db_side', 3);
INSERT INTO license_renewals VALUES (2, 2, 2019, 230.00, 'db_side', 3);
INSERT INTO license_renewals VALUES (3, 3, 2019, 50.00, 'db_side', 3);   -- Alvarez Home Bakery: db-side path, no surcharge applied
INSERT INTO license_renewals VALUES (4, 4, 2019, 75.00, 'screen_side', 3); -- Chen Tutoring Services: screen-side path, surcharge applied
INSERT INTO license_renewals VALUES (5, 5, 2019, 175.00, 'db_side', 3);
INSERT INTO license_renewals VALUES (6, 6, 2019, 0.00, 'db_side', 3);
INSERT INTO license_renewals VALUES (7, 3, 2020, 50.00, 'db_side', 5);
INSERT INTO license_renewals VALUES (8, 4, 2020, 75.00, 'screen_side', 5);

-- Inspections -- includes the two conflicting exemption reasons
INSERT INTO inspections VALUES (1, 3, '2015-02-15', '2015-02-20', 1, 'per standard practice');
INSERT INTO inspections VALUES (2, 4, '2017-05-25', NULL, 1, 'per Ordinance 2009-14');
INSERT INTO inspections VALUES (3, 6, '2012-12-05', '2012-12-10', 1, 'per Ordinance 2009-14');
INSERT INTO inspections VALUES (4, 1, '2005-03-15', '2005-03-18', 0, NULL);
INSERT INTO inspections VALUES (5, 2, '2006-07-28', '2006-08-01', 0, NULL);
