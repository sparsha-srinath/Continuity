"""Print the code-level fee conflict and historical type-C records."""

import sqlite3
from pathlib import Path

from business_rules import calculate_renewal_fee_db_side
from screen_license_renewal import calculate_renewal_fee_screen_side


ROOT = Path(__file__).resolve().parent.parent
DATABASE = ROOT / "db" / "blpts.db"


def main() -> None:
    print("BLPTS renewal fee comparison for 2022")
    print("Type | DB side | Screen side | Result")
    print("-----+---------+-------------+--------")
    for license_type in "ABCDE":
        db_fee = calculate_renewal_fee_db_side(license_type, 2022)
        screen_fee = calculate_renewal_fee_screen_side(license_type, 2022)
        result = "MISMATCH" if db_fee != screen_fee else "OK"
        print(f"  {license_type}  | ${db_fee:6.2f} | ${screen_fee:9.2f} | {result}")

    if not DATABASE.exists():
        print(f"\nHistorical database not found: {DATABASE}")
        return

    print("\nHistorical type-C renewals")
    with sqlite3.connect(DATABASE) as connection:
        rows = connection.execute(
            """
            SELECT r.renewal_id, l.business_name, r.renewal_year,
                   r.fee_charged, r.calculated_by
            FROM license_renewals AS r
            JOIN licenses AS l ON l.license_id = r.license_id
            WHERE l.license_type = 'C' AND r.renewal_year >= 2019
            ORDER BY r.renewal_year, r.renewal_id
            """
        ).fetchall()
    for renewal_id, business_name, year, fee, calculated_by in rows:
        print(f"{renewal_id}: {business_name} | {year} | ${fee:.2f} | {calculated_by}")


if __name__ == "__main__":
    main()