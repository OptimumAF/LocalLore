//! A bounded host contract proof. No database, native inference, networking or mobile adapter.
pub mod context_compiler;
pub mod contracts;
pub mod engine;
pub use engine::author_correction;
#[cfg(feature = "host")]
pub mod host;
pub mod inference;
#[cfg(feature = "host")]
pub mod inspection;
pub mod inspection_query;
pub mod intent_guard;
pub mod memory_coverage;
pub mod play;
#[cfg(feature = "host")]
mod player_presentation_v2;
pub mod scope;
pub mod story_authoring;
pub mod story_presentation;
pub mod story_setup;
pub mod turn_capture;
pub mod turn_trace;
