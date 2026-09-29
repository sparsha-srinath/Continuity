"""
inspection_rules.py

Modernized inspection exemption logic. Resolved during discovery via
correspondence with the County Clerk's Office (R. Colston, 2026-03-11,
BLPTS-DISC-2): the exemption is based on Ordinance 2009-14, Section 3(b).

See ADD "Decision 2".
"""

EXEMPT_LICENSE_TYPES = ("C", "E")
EXEMPTION_SOURCE = "Ordinance 2009-14, Section 3(b)"

def is_inspection_exempt(license_type: str) -> bool:
    return license_type in EXEMPT_LICENSE_TYPES
