# Architecture Decision Document -- BLPTS Modernization Phase 1
**Author:** K. Ibarra, Applications Developer
**Date:** 2026-04-02
**Status:** Accepted

## Decision 1: Unify fee calculation into a single function
**Context:** Legacy maintained two independent implementations of the
renewal fee calculation (a database-side stored procedure and an
on-screen calculation). A 2018 patch (LOG-441) was applied to only the
screen-side path, causing the two to silently diverge for Home
Occupation (type C) renewals -- confirmed during discovery as
BLPTS-DISC-1.

**Decision:** Implement one function, `calculate_base_fee()`, as the
single source of truth for renewal fee calculation. No other module may
independently compute this value.

**Consequences:** Eliminates the class of bug where a patch applied to
one path doesn't propagate to another. Historical fee amounts prior to
this change remain as recorded and are not retroactively corrected.

## Decision 2: Codify the inspection exemption explicitly, with a named source
**Context:** Legacy exempted license types C and E from the 30-day
inspection rule with no confirmed rationale on file (BLPTS-DISC-2).
Resolved during discovery via correspondence with the County Clerk's
Office: the exemption is based on Ordinance 2009-14, Section 3(b).

**Decision:** Hardcode the exemption with an explicit reference constant
(`EXEMPTION_SOURCE = "Ordinance 2009-14, Section 3(b)"`) rather than a
bare boolean check, so the rationale is visible directly in the code
rather than requiring external lookup.

**Consequences:** Any future engineer reading this code sees the legal
basis immediately. If the ordinance is amended, this constant is the
single place to update.

## Decision 3: Introduce multi-year renewal as a new, additive feature
**Context:** No legacy equivalent exists. Clerk's office requested a way
to reduce annual renewal overhead for businesses that would prefer to
renew less frequently.

**Decision:** Support 1, 2, or 3-year renewal terms with discounts of 0%,
5%, and 10% respectively, calculated as a percentage off the multi-year
base total (not a flat per-year discount).

**Consequences:** This is a genuinely new capability with no legacy
precedent -- it should never be described as a "fix" or "restoration" of
prior behavior when referenced going forward.
