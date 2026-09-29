"""Confirmed inspection exemption rule for modernized BLPTS."""

EXEMPT_LICENSE_TYPES = ("C", "E")
EXEMPTION_SOURCE = "Ordinance 2009-14, Section 3(b)"


def is_inspection_exempt(license_type: str) -> bool:
    return license_type in EXEMPT_LICENSE_TYPES
