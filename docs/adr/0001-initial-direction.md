# ADR-0001 — Initial execution direction

Status: **proposed**. Date: 2026-10-22. Related tasks: M01, M02, M03. Decision authority: @OptimumAF.

## Context

The requested product is a new fully local phone storyteller with progressive player state, short/long story memory, a character interaction network, and durable consequences. The repository begins with documentation only. No reference phone, RAM tier, model/runtime measurement, or implementation is confirmed.

## Proposed direction

Android first; Kotlin/Compose for the phone interface; a portable Rust domain/persistence engine; SQLite with typed event history and validated projections; one local inference backend chosen by measurement; one loaded model for several sequential roles; exact/lexical retrieval before embeddings; independent stories and explicit branches; no executable story-pack plug-ins.

The engine validates state changes and the model provides creative proposals/prose. Fact/belief/statement separation and branch/observer eligibility are core contracts, not afterthoughts. The first playable acceptance scene is the scarce-potion/private-knowledge example.

## Alternatives

A Kotlin-only engine simplifies initial Android integration but may require more porting work. A cross-platform UI can accelerate an eventual second platform but should not obscure native inference/lifecycle constraints. A chatbot with large rolling summaries is simpler but cannot provide the same mechanical/provenance controls. Multiple models or a graph/vector service add complexity before evidence of benefit.

## Consequences and validation

Native FFI, mobile packaging, and SQLite ownership need an early spike. Model quality and complete-turn latency are the largest feasibility risks. A small fake-provider harness should support independent domain/UI work while physical-device tests remain explicit. M01 selects the runtime/profile and can recommend revising this proposal.

## Acceptance

Not yet accepted as a final measured architecture. Record the owner-approved decision and supporting experiments in a successor/update after M01/M02. Do not mark feasibility complete because this document exists.
