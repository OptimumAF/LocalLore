# ADR-0009: Retire playable parents while preserving original ancestry

Status: implemented, pending owner acceptance. Refs #12 (M08.05, supporting
M08.01/M08.04/M08.06). No dependency, backend or local-only policy change.

## Context

A retained child needs its ancestors' accepted history through each fork.
Deleting every parent row breaks that history; copying it into a child would
change original request scopes and provenance. Hiding a parent only in Compose
also leaves stale native sessions and import able to reopen it. M08.05 requires
safe shared ancestry, rather than substituting leaf-only deletion.

## Decision

Schema3 adds persistent branch-ID tombstones. Public target admission rejects
retired IDs before cached replies, retries, reads and writes. A private Store
reader can still replay original retained ancestor receipts for active children.
An ID remains reserved after its physical rows are collected. Root deletion
continues to mean whole-story deletion; roots cannot be individually retired.

Retirement keeps only the original completed prefix needed by physical retained
children, including a parent's own birth fork. It removes unreachable local
tail, noncommitted work and derived data. Retired leaf ancestors are collected
recursively. All surviving active branches must retain identical canonical
bytes and receipts. Preview, stale-consent checks, revalidation, row counts,
foreign keys and mutation occur in one Store transaction; failures roll back.

Native deletion shares the session-creating/committing mutation gate. After the
Store commit, it invalidates only retired/collected target sessions before
releasing the gate. Active child and sibling sessions remain usable. Generation
stays outside this gate and its completion is fenced by Host session identity.

Archivev2 preserves the retired-ID set and physical retained prefixes without
rewriting scopes. Unretired stories still export v1. Historical v1/source
schema1/2 readers remain supported. Catalogv2 includes retired physical rows so
clients validate the original graph before filtering playable choices.

## Alternatives and consequences

Refusing parent deletion until every descendant is removed fails the retained
child criterion. Reparenting or duplicating receipts creates a new provenance
model. Cascading deletion removes user-selected retained stories. A UI-only flag
cannot fence other native owners. Persistent tombstones cost a bounded namespace
slot: physical and reserved IDs together remain limited to256 per story.

Exact schema1/2 upgrades require a new, consistent backup before migration.
Existing/future/foreign schema rejection and nonoverwrite backup rules remain.
Backups and exports are private plaintext data outside logical deletion; no
forensic-erasure guarantee or automatic destructive restore is introduced.

Checksums establish archive integrity, not authorship. A deliberate author can
rewrite history and recompute a checksum; v2 does not authenticate all historical
deletion intent. The supported promise is validated normal form and faithful
roundtrip of an unchanged archive, not tamper-proof provenance.

See the [contract](../native/PARENT_RETENTION_CONTRACT.md) and dated verification
for executed tests and limits. Large-history CPU deadlines, physical phones,
ARM64 execution, real-model performance and a branch-creation UI remain separate.
