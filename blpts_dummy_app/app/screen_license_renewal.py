"""
screen_license_renewal.py

Originally the PowerScript "ue_calc_fee" event handler embedded in the
w_license_renewal DataWindow. Rewritten here as a Python stand-in.

In 2018 D. Marsh patched this file only for Home Occupation Plus (BLPTS-441),
adding a $25 surcharge for type C renewals. The stored-procedure stand-in was
not updated, so the two paths intentionally disagree.
"""


def calculate_renewal_fee_screen_side(license_type: str, renewal_year: int) -> float:
    """Calculate the on-screen renewal fee, including the 2018 type-C patch."""
    base_fees = {"A": 150.00, "B": 200.00, "C": 50.00, "D": 175.00, "E": 0.00}
    fee = base_fees.get(license_type, 100.00)
    if renewal_year >= 2011 and license_type in ("A", "B"):
        fee = fee * 1.15
    if renewal_year >= 2018 and license_type == "C":
        fee = fee + 25.00
    return round(fee, 2)