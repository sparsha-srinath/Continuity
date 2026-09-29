"""
screen_license_renewal.py

Originally the PowerScript "ue_calc_fee" event handler embedded in the
w_license_renewal DataWindow (the on-screen renewal form). Rewritten
here in Python as a stand-in for prototyping.

Maintainer history (from code comments -- again, no formal changelog):
    - Original logic mirrored business_rules.py at time of writing (2003).
    - 2018 patch: D. Marsh (in-house, hired 2016, departed 2020).
      Bug ticket BLPTS-441: Home Occupation (C) renewals were being
      charged $50.00 flat even for businesses that had upgraded to a
      "Home Occupation Plus" designation (higher square footage,
      allowed per Ordinance 2016-03). D. Marsh patched THIS FILE ONLY
      to add a $25 surcharge for license type C, effective 2018+.
      Did not update business_rules.py / sp_calc_renewal_fee, and no
      one flagged the two paths were now producing different numbers
      for the same license type.
"""

def calculate_renewal_fee_screen_side(license_type: str, renewal_year: int) -> float:
    """
    Calculates the renewal fee as shown to the clerk on the renewal
    screen before the county's e-check payment step.
    """
    base_fees = {
        "A": 150.00,
        "B": 200.00,
        "C": 50.00,
        "D": 175.00,
        "E": 0.00,
    }

    fee = base_fees.get(license_type, 100.00)

    if renewal_year >= 2011 and license_type in ("A", "B"):
        fee = fee * 1.15

    # D.M. 2018 patch (BLPTS-441) -- Home Occupation Plus surcharge.
    # Applied here at the screen level only; sp_calc_renewal_fee was
    # never updated to match. See ticket BLPTS-441 for context.
    if renewal_year >= 2018 and license_type == "C":
        fee = fee + 25.00

    return round(fee, 2)
