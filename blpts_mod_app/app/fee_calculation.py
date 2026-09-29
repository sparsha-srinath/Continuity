"""Unified modernized renewal fee calculation."""

BASE_FEES = {"A": 150.00, "B": 200.00, "C": 50.00, "D": 175.00, "E": 0.00}


def calculate_base_fee(license_type: str, renewal_year: int) -> float:
    fee = BASE_FEES.get(license_type, 100.00)
    if renewal_year >= 2011 and license_type in ("A", "B"):
        fee = fee * 1.15
    if license_type == "C":
        fee = fee + 25.00
    return round(fee, 2)
