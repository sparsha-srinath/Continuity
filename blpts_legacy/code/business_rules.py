"""
business_rules.py

Originally implemented as a Sybase SQL Anywhere stored procedure
(sp_calc_renewal_fee) circa 2003. Rewritten here in Python as a
stand-in for prototyping -- logic and comments preserve the original
intent and patch history as closely as possible.

Maintainer history (from code comments, not a formal changelog --
BLPTS never had one):
    - Original author: T. Whitfield (contractor, PB Solutions Group)
      contract ended 2015, no forwarding contact on file.
    - 2011 patch: T. Whitfield, per Ordinance 2011-07 fee increase.
    - No further changes to this file after 2015.
"""

def calculate_renewal_fee_db_side(license_type: str, renewal_year: int) -> float:
    """
    Calculates the license renewal fee.

    NOTE (T.W., 2011): Ordinance 2011-07 raised base fees for license
    types A and B by 15%, effective renewal_year >= 2011. Home
    Occupation (C) and Non-Profit (E) were explicitly EXEMPTED from
    this increase per the ordinance -- see Ordinance 2011-07 text on
    file (partial only, page 2 missing from county archive).
    """
    base_fees = {
        "A": 150.00,  # Retail
        "B": 200.00,  # Food Service
        "C": 50.00,   # Home Occupation
        "D": 175.00,  # Contractor
        "E": 0.00,    # Non-Profit -- exempt from base fee entirely
    }

    fee = base_fees.get(license_type, 100.00)

    if renewal_year >= 2011 and license_type in ("A", "B"):
        fee = fee * 1.15  # Ordinance 2011-07 increase

    return round(fee, 2)
