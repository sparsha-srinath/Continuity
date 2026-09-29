"""Demonstrate the corrected fee, new discount, and cited inspection rule."""

from fee_calculation import calculate_base_fee
from inspection_rules import EXEMPTION_SOURCE
from renewal_discount import calculate_multi_year_total


if __name__ == "__main__":
    print(f"Unified type-C fee for 2026: ${calculate_base_fee('C', 2026):.2f}")
    print(f"Type-A three-year renewal: {calculate_multi_year_total('A', 2026, 3)}")
    print(f"Inspection exemption source: {EXEMPTION_SOURCE}")
