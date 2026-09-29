"""
inspection_scheduler.py

Originally the w_inspection_schedule window's PowerScript logic governing the
30-day post-application inspection rule. No comment in the original source
explains why license types C and E are exempt. The exemption predates every
current staff member's tenure. Ordinance 2009-14 may explain it, or it may be
a bug left behind by T. Whitfield; neither theory is confirmed.
"""


def is_inspection_exempt(license_type: str) -> bool:
    return license_type in ("C", "E")