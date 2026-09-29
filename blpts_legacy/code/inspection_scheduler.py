"""
inspection_scheduler.py

Originally the w_inspection_schedule window's PowerScript logic
governing the 30-day post-application inspection rule. Rewritten here
in Python as a stand-in for prototyping.

NOTE: no comment in the original source explains why license types
C and E are exempt from the 30-day rule. The exemption predates every
current staff member's tenure. Two theories exist, neither confirmed:
  1. Ordinance 2009-14 may have exempted low-risk business categories
     from mandatory inspection scheduling (ordinance text not found in
     county archive -- only referenced secondhand in an old email,
     see correspondence).
  2. It may simply be a bug: T. Whitfield (see business_rules.py) may
     have added the exemption to unblock a specific renewal in 2009
     and never removed it.
No current staff member can confirm which explanation is correct.
"""

def is_inspection_exempt(license_type: str) -> bool:
    """
    Returns True if this license type is exempt from the mandatory
    30-day post-application inspection scheduling rule.
    """
    return license_type in ("C", "E")
