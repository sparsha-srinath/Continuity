"""
renewal_discount.py

NEW FEATURE -- has no legacy equivalent. See ADD "Decision 3" and ticket
BLPTS-MOD-13.

Discount schedule:
    1-year renewal: no discount
    2-year renewal: 5% off the total (2x base fee)
    3-year renewal: 10% off the total (3x base fee)
"""

from fee_calculation import calculate_base_fee

DISCOUNT_RATES = {1: 0.00, 2: 0.05, 3: 0.10}

def calculate_multi_year_total(license_type: str, renewal_year: int, term_years: int) -> dict:
    if term_years not in DISCOUNT_RATES:
        raise ValueError("term_years must be 1, 2, or 3")

    per_year_fee = calculate_base_fee(license_type, renewal_year)
    base_total = per_year_fee * term_years
    discount_rate = DISCOUNT_RATES[term_years]
    discount_amount = round(base_total * discount_rate, 2)
    final_total = round(base_total - discount_amount, 2)

    return {
        "base_total": round(base_total, 2),
        "discount_amount": discount_amount,
        "final_total": final_total,
    }
