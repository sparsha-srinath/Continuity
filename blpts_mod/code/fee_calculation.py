"""
fee_calculation.py

Modernized, unified renewal fee calculation. Replaces the two divergent
legacy code paths (sp_calc_renewal_fee and the w_license_renewal
DataWindow script) with a single source of truth.

See ADD "Decision 1" and ticket BLPTS-MOD-12 (resolves BLPTS-DISC-1).
"""

BASE_FEES = {
    "A": 150.00,
    "B": 200.00,
    "C": 50.00,
    "D": 175.00,
    "E": 0.00,
}

def calculate_base_fee(license_type: str, renewal_year: int) -> float:
    fee = BASE_FEES.get(license_type, 100.00)
    if renewal_year >= 2011 and license_type in ("A", "B"):
        fee = fee * 1.15
    if license_type == "C":
        # Home Occupation Plus surcharge, correctly applied everywhere now.
        fee = fee + 25.00
    return round(fee, 2)
