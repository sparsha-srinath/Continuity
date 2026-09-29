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
    """Calculate the database-side license renewal fee."""
    base_fees = {"A": 150.00, "B": 200.00, "C": 50.00, "D": 175.00, "E": 0.00}
    fee = base_fees.get(license_type, 100.00)
    if renewal_year >= 2011 and license_type in ("A", "B"):
        fee = fee * 1.15
    return round(fee, 2)