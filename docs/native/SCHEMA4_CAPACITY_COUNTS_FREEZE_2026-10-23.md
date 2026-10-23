# Schema4 relief count freeze — 2026-10-23

The coordinator approved this narrow source change after reviewing the actual fixed32 measurement at `cd96867691e1f3419d250c155619f6706b0c158c`, preserved in [calibration evidence](SCHEMA4_CAPACITY_CALIBRATION_2026-10-23.md). Current reference remains initial23/schema4/full schema digest `e9f19f3b384c52c5c7bd360e23c1db9e76314152f750a5b9f07f7a14071f8362`.

The exact expected padding rows/Full attempt/freed pages change **14/15/15 → 8/9/9** across the owned Host example, fixed Python helper fault/readiness gates, Android profile/Gradle/manifest/helper guards and synthetic manifest checks. An additional old14-row metadata rejection is retained alongside the prior incorrect16-row case. There is no cap, payload, operation, original request, seed, deadline, output bound, helper ownership, cleanup, fault selector, callback or native/Host oracle change. Relief remains32 pages and3500-byte zero payload; full capacity remains23.

The old14/15 initial run remains an actual failure (`measured_fill_profile`) before Host commit gates, with successful owned cleanup8/free9 and unchanged local logs/stdout. Current source is frozen before attempting the full green workflow. The measurement does not qualify Android SQLite: this freeze aligns its static profile only, with no ADB/device/app operation.

A local editing pass briefly misdecoded the UTF-8 middle dot in two manifest labels using the default Windows codepage; diff inspection corrected it before commit/test. Final label bytes retain the intended middle dot and v4 identity; no changed label is accepted by weakening an audit. Future file reads in this packet use explicit UTF-8.

Coordinator retains the heavy build slot for Rust/Android checks. Only pure Python synthetic guards may run before the next explicit resource release. Subsequent exact-source results, failure retention and missing broad gates will be recorded separately; no full M04/M07/D08/D09 acceptance is claimed.
