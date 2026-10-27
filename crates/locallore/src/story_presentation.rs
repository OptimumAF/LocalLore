//! Initial story presentation configuration, never a fact or mechanical privilege.
use serde::{Deserialize, Serialize};
use std::collections::BTreeSet;

pub const MAX_EXCLUDED_PHRASES: usize = 8;
pub const MAX_PHRASE_SCALARS: usize = 64;
pub const MAX_PHRASE_BYTES: usize = 256;
pub const MAX_PHRASE_TOTAL_BYTES: usize = 1024;

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
#[cfg_attr(feature = "host", derive(schemars::JsonSchema))]
pub enum StoryTone {
    #[default]
    Plain,
    Warm,
    Brisk,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
#[cfg_attr(feature = "host", derive(schemars::JsonSchema))]
pub struct StoryPresentationV1 {
    pub version: u16,
    pub tone: StoryTone,
    pub excluded_phrases: Vec<String>,
}

impl Default for StoryPresentationV1 {
    fn default() -> Self {
        Self {
            version: 1,
            tone: StoryTone::Plain,
            excluded_phrases: Vec::new(),
        }
    }
}

impl StoryPresentationV1 {
    pub fn is_default(&self) -> bool {
        self == &Self::default()
    }

    /// Validation never trims, normalizes, sorts or changes the reviewed input.
    pub fn validate(&self) -> bool {
        if self.version != 1 || self.excluded_phrases.len() > MAX_EXCLUDED_PHRASES {
            return false;
        }
        let mut bytes = 0usize;
        let mut seen = BTreeSet::new();
        for phrase in &self.excluded_phrases {
            if phrase.is_empty() || phrase.trim() != phrase
                || phrase.len() > MAX_PHRASE_BYTES
                || phrase.chars().count() > MAX_PHRASE_SCALARS
                || phrase.chars().any(|c| c.is_control()
                    || matches!(c, '\u{2028}' | '\u{2029}' | '\u{202a}'..='\u{202e}' | '\u{2066}'..='\u{2069}'))
                || !seen.insert(phrase.to_lowercase()) {
                return false;
            }
            let Some(total) = bytes.checked_add(phrase.len()) else {
                return false;
            };
            bytes = total;
        }
        bytes <= MAX_PHRASE_TOTAL_BYTES
    }

    /// Unicode lowercase literal substring matching, not normalization or full casefold.
    /// This constrains generated narration; it does not censor source truth or player text.
    pub fn allows_narration(&self, text: &str) -> bool {
        if !self.validate() {
            return false;
        }
        let lower = text.to_lowercase();
        self.excluded_phrases
            .iter()
            .all(|phrase| !lower.contains(&phrase.to_lowercase()))
    }
}
