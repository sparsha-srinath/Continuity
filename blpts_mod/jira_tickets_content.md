# Jira tickets to create (mod build phase, present-day)

## BLPTS-MOD-12
**Summary:** Consolidate fee calculation logic (resolves BLPTS-DISC-1)
**Assignee:** K. Ibarra (Applications Developer)
**Labels:** modernization, fee-calculation, resolves-BLPTS-DISC-1
**Description:**
Legacy system maintained two separate fee calculation paths that
diverged after a 2018 patch was applied to only one of them. This ticket
consolidates both into a single unified calculation module
(fee_calculation.py), eliminating the possibility of future drift.

## BLPTS-MOD-13
**Summary:** Implement multi-year renewal discount
**Assignee:** K. Ibarra (Applications Developer)
**Labels:** modernization, new-feature
**Description:**
New feature, no legacy equivalent. Allows businesses to renew licenses
for 2 or 3 years at once, with a 5% or 10% discount respectively,
reducing annual renewal overhead for both businesses and the clerk's
office.
