INSERT INTO staff VALUES
    (1, 'T. Whitfield', 'Original Developer', '2003-01-15', '2015-12-31', 'contractor_ended'),
    (2, 'D. Marsh', 'Applications Developer', '2016-02-01', '2020-08-31', 'departed'),
    (3, 'R. Colston', 'Clerk Supervisor', '2010-06-14', NULL, 'active'),
    (4, 'J. Pae', 'IT Support', '2019-03-04', NULL, 'active'),
    (5, 'M. Alvarez', 'Senior Licensing Clerk', '2012-09-10', NULL, 'active');

INSERT INTO ordinances VALUES
    (1, 2011, 'Ordinance 2011-07', 'Raises renewal fees by 15% for license types A and B; page 2 is missing from the county archive.', 'A,B', 'partial'),
    (2, 2016, 'Ordinance 2016-03', 'Creates a new Home Occupation Plus designation for license type C.', 'C', 'yes'),
    (3, 2009, 'Ordinance 2009-14', 'Referenced in staff correspondence as a possible source of inspection exemptions for low-risk business categories; full text not located in county archive.', 'C,E', 'no');

INSERT INTO fee_schedule VALUES
    (1, 'A', 150.00, 2003, 1, 'Original schedule'),
    (2, 'B', 200.00, 2003, 1, 'Original schedule'),
    (3, 'C', 50.00, 2003, 1, 'Original schedule'),
    (4, 'D', 175.00, 2003, 1, 'Original schedule'),
    (5, 'E', 0.00, 2003, 1, 'Original schedule');

INSERT INTO licenses VALUES
    (101, 'Maple Street Mercantile', 'A', '2005-04-12', 'active'),
    (102, 'Harborview Cafe', 'B', '2008-07-21', 'active'),
    (103, 'Willow Lane Pottery', 'C', '2012-05-03', 'active'),
    (104, 'North County Electric', 'D', '2017-09-18', 'active'),
    (105, 'Civic Arts Outreach', 'E', '2020-01-27', 'active'),
    (106, 'Juniper Home Studio', 'C', '2022-06-11', 'active');

INSERT INTO license_renewals VALUES
    (1001, 103, 2014, 50.00, 'db_side', 3),
    (1002, 103, 2019, 50.00, 'db_side', 3),
    (1003, 106, 2019, 75.00, 'screen_side', 3),
    (1004, 101, 2018, 172.50, 'db_side', 3),
    (1005, 102, 2020, 230.00, 'screen_side', 5),
    (1006, 104, 2021, 175.00, 'db_side', 5),
    (1007, 105, 2021, 0.00, 'db_side', 5),
    (1008, 101, 2022, 172.50, 'screen_side', 3),
    (1009, 102, 2022, 230.00, 'db_side', 3);

INSERT INTO inspections VALUES
    (2001, 101, '2022-02-10', '2022-02-22', 0, NULL),
    (2002, 103, NULL, NULL, 1, 'per standard practice'),
    (2003, 105, NULL, NULL, 1, 'per Ordinance 2009-14'),
    (2004, 104, '2023-03-05', '2023-03-20', 0, NULL),
    (2005, 106, NULL, NULL, 1, 'home occupation desk review');