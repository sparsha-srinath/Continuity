# BLPTS System Overview
**Document owner:** T. Whitfield, PB Solutions Group (contractor)
**Last updated:** August 2009
**Status:** Internal reference -- County Clerk's Office

## Purpose
BLPTS (Business License & Permit Tracking System) is the county's system of
record for issuing and renewing business licenses, tracking permit fees,
and scheduling required inspections. Built in PowerBuilder 9 against a
Sybase SQL Anywhere backend, deployed 2003.

## License types
- **A** -- Retail
- **B** -- Food Service
- **C** -- Home Occupation
- **D** -- Contractor
- **E** -- Non-Profit

## Modules
- **w_license_renewal** -- the on-screen renewal form clerks use daily.
  Calculates the renewal fee for display before payment.
- **sp_calc_renewal_fee** -- database-side stored procedure performing the
  same calculation, used by the nightly batch reconciliation job.
- **w_inspection_schedule** -- governs the 30-day post-application
  inspection rule and tracks exemptions.

## Known limitations (as of this writing)
- No formal source control; working copies are periodically archived to
  the shared drive as zip files.
- Fee schedule changes are hardcoded per ordinance year rather than driven
  by a rates table.
- Single-contractor maintenance model -- PB Solutions Group is the sole
  maintainer of this system.
