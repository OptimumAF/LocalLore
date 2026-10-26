// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Read-only, player-visible starter review and validated explicit creation input.
//! A preview is not a world edit, a model request, or an arbitrary seed import.
use crate::{contracts::Seed, engine::Engine};
use serde::Serialize;
use sha2::{Digest, Sha256};

pub const TEMPLATE: &str = "lantern-quay-v1";
pub const MAX_TITLE_SCALARS: usize = 80;
const SEED: &[u8] = include_bytes!("../../../fixtures/lantern_quay.json");

#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct StoryTemplatePreviewV1 {
    pub version: u16,
    pub template: String,
    pub seed_sha256: String,
    pub default_title: String,
    pub description: String,
    pub profile: String,
    pub details: Vec<String>,
}

/// Constructed only after the closed named-creation input passes native validation.
/// This has no serde implementation: callers cannot deserialize a replacement Seed.
pub struct NamedStarter {
    seed: Seed,
    title: String,
}
impl NamedStarter {
    pub fn seed(&self) -> &Seed {
        &self.seed
    }
    pub fn title(&self) -> &str {
        &self.title
    }
}

pub fn valid_title(title: &str) -> bool {
    !title.is_empty() && title.trim() == title && title.chars().count() <= MAX_TITLE_SCALARS &&
        title.len() <= 320 && !title.chars().any(|c| c.is_control() ||
            matches!(c, '\u{2028}' | '\u{2029}' | '\u{202a}'..='\u{202e}' | '\u{2066}'..='\u{2069}'))
}

fn seed_hash() -> String {
    format!("{:x}", Sha256::digest(SEED))
}
fn bundled_seed(template: &str) -> Result<Seed, &'static str> {
    if template != TEMPLATE {
        return Err("UnsupportedSeed");
    }
    let seed: Seed = serde_json::from_slice(SEED).map_err(|_| "Integrity")?;
    if seed.id != TEMPLATE || seed.scope.branch != "main" {
        return Err("Integrity");
    }
    Engine::new(seed.clone()).map_err(|_| "Integrity")?;
    Ok(seed)
}

pub fn prepare_named(
    template: &str,
    expected_hash: &str,
    title: &str,
    creation_id: &str,
) -> Result<NamedStarter, &'static str> {
    let mut seed = bundled_seed(template)?;
    if expected_hash != seed_hash() {
        return Err("Stale");
    }
    if !valid_title(title) {
        return Err("InvalidTitle");
    }
    if creation_id.len() != 32
        || !creation_id
            .bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
    {
        return Err("InvalidInput");
    }
    seed.scope.story = format!("quay-{creation_id}");
    seed.scope.branch = "main".into();
    Ok(NamedStarter {
        seed,
        title: title.into(),
    })
}

pub fn template_preview(template: &str) -> Result<StoryTemplatePreviewV1, &'static str> {
    let seed = bundled_seed(template)?;
    let engine = Engine::new(seed.clone()).map_err(|_| "Integrity")?;
    let visible = engine
        .character_context(&seed.player, engine.scope(), 0)
        .map_err(|_| "Integrity")?;
    let actor = &visible.self_state;
    let mut details = vec![
        format!("Player: {}", actor.name),
        format!("Location: {}", actor.location),
        format!("Alive: {}", actor.alive),
        format!("Energy: {}", actor.energy),
        format!("Story time: {}", seed.story_time),
    ];
    details.extend(
        actor
            .attributes
            .iter()
            .map(|(id, value)| format!("Attribute {id}: {value}")),
    );
    details.extend(
        actor
            .abilities
            .iter()
            .map(|(id, rank)| format!("Ability {id}: rank {rank}")),
    );
    details.extend(actor.injuries.iter().map(|id| format!("Injury: {id}")));
    details.extend(
        actor
            .affiliations
            .iter()
            .map(|id| format!("Affiliation: {id}")),
    );
    details.extend(actor.goals.iter().map(|id| format!("Goal: {id}")));
    for (id, item) in &seed.items {
        if item.owner == seed.player {
            let loan = item
                .return_to
                .as_ref()
                .map(|to| format!("; return to {to}"))
                .unwrap_or_default();
            details.push(format!("Inventory {id}: {}{loan}", item.quantity));
        }
    }
    details.extend(
        visible
            .facts
            .iter()
            .map(|(id, text)| format!("Known fact {id}: {text}")),
    );
    details.extend(
        visible
            .beliefs
            .iter()
            .map(|belief| format!("Belief: {}", belief.proposition)),
    );
    for (id, promise) in &seed.commitments {
        if promise.from == seed.player {
            details.push(format!(
                "Commitment {id} to {}: {} (due at {})",
                promise.to, promise.terms, promise.deadline
            ));
        }
    }
    for relationship in &seed.relationships {
        if relationship.from == seed.player {
            details.push(format!(
                "Your relationship to {}: respect {}, trust {}, obligation {}",
                relationship.to, relationship.respect, relationship.trust, relationship.obligation
            ));
        }
    }
    let preview = StoryTemplatePreviewV1 { version: 1, template: TEMPLATE.into(), seed_sha256: seed_hash(),
        default_title: "Lantern Quay".into(),
        description: "An original local starter set at Lantern Quay. Review your starting facts below, then choose how the story develops.".into(),
        profile: match seed.profile {
            crate::contracts::Profile::FantasyV1 => "fantasy_v1",
            crate::contracts::Profile::NarrativeV1 => "narrative_v1",
        }.into(), details };
    if preview.details.len() > 64
        || preview.details.iter().any(|line| line.len() > 2048)
        || serde_json::to_vec(&preview).map_err(|_| "Integrity")?.len() > 16384
    {
        return Err("TooLarge");
    }
    Ok(preview)
}
