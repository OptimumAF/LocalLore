// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Read-only, player-visible starter review and validated explicit creation input.
//! A preview is not a world edit, a model request, or an arbitrary seed import.
use crate::{
    contracts::{Confidence, Evidence, Seed},
    engine::Engine,
};
use serde::Serialize;
use sha2::{Digest, Sha256};

pub const TEMPLATE: &str = "lantern-quay-v1";
pub const MAX_TITLE_SCALARS: usize = 80;
pub const MAX_PLAYER_NAME_SCALARS: usize = 64;
pub const MAX_PLAYER_NAME_BYTES: usize = 256;
pub const NARRATIVE_TEMPLATE: &str = "bracken-harbor-v1";
struct Template {
    id: &'static str,
    bytes: &'static [u8],
    title: &'static str,
    description: &'static str,
}
const TEMPLATES: &[Template] = &[
    Template {
        id: TEMPLATE,
        bytes: include_bytes!("../../../fixtures/lantern_quay.json"),
        title: "Lantern Quay",
        description: "An original local starter set at Lantern Quay. Review your starting facts below, then choose how the story develops.",
    },
    Template {
        id: NARRATIVE_TEMPLATE,
        bytes: include_bytes!("../../../fixtures/bracken_harbor.json"),
        title: "Bracken Harbor",
        description: "An original local starter at Bracken Harbor. Keep a borrowed lantern safe, help the harbor neighbors, and decide what to do about a missing ferry ledger.",
    },
];

#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct StoryTemplateDescriptorV1 {
    pub template: String,
    pub default_title: String,
    pub description: String,
    pub profile: String,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct StoryTemplateCatalogV1 {
    pub version: u16,
    pub templates: Vec<StoryTemplateDescriptorV1>,
}

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

#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct StorySetupPreviewV1 {
    pub version: u16,
    pub template: String,
    pub template_sha256: String,
    pub setup_sha256: String,
    pub default_title: String,
    pub description: String,
    pub profile: String,
    pub player_name: String,
    pub details: Vec<String>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct StoryPresentationPreviewV1 {
    pub version: u16,
    pub template: String,
    pub template_sha256: String,
    pub setup_sha256: String,
    pub default_title: String,
    pub description: String,
    pub profile: String,
    pub player_name: String,
    pub presentation: crate::story_presentation::StoryPresentationV1,
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

pub fn valid_player_name(name: &str) -> bool {
    valid_title(name)
        && name.chars().count() <= MAX_PLAYER_NAME_SCALARS
        && name.len() <= MAX_PLAYER_NAME_BYTES
}

fn definition(template: &str) -> Result<&'static Template, &'static str> {
    TEMPLATES
        .iter()
        .find(|entry| entry.id == template)
        .ok_or("UnsupportedSeed")
}
fn seed_hash(template: &str) -> Result<String, &'static str> {
    Ok(format!("{:x}", Sha256::digest(definition(template)?.bytes)))
}
fn profile_name(profile: &crate::contracts::Profile) -> &'static str {
    match profile {
        crate::contracts::Profile::FantasyV1 => "fantasy_v1",
        crate::contracts::Profile::NarrativeV1 => "narrative_v1",
    }
}
fn bundled_seed(template: &str) -> Result<Seed, &'static str> {
    let seed: Seed =
        serde_json::from_slice(definition(template)?.bytes).map_err(|_| "Integrity")?;
    if seed.id != template || seed.scope.branch != "main" {
        return Err("Integrity");
    }
    Engine::new(seed.clone()).map_err(|_| "Integrity")?;
    Ok(seed)
}

/// Only public starter metadata. No session, storage, inference or full Seed is exposed.
pub fn template_catalog() -> Result<StoryTemplateCatalogV1, &'static str> {
    let mut templates = Vec::new();
    for template in TEMPLATES {
        let seed = bundled_seed(template.id)?;
        templates.push(StoryTemplateDescriptorV1 {
            template: template.id.into(),
            default_title: template.title.into(),
            description: template.description.into(),
            profile: profile_name(&seed.profile).into(),
        });
    }
    let catalog = StoryTemplateCatalogV1 {
        version: 1,
        templates,
    };
    if catalog.templates.is_empty()
        || catalog.templates.len() > 8
        || serde_json::to_vec(&catalog).map_err(|_| "Integrity")?.len() > 16384
    {
        return Err("TooLarge");
    }
    Ok(catalog)
}

pub fn prepare_named(
    template: &str,
    expected_hash: &str,
    title: &str,
    creation_id: &str,
) -> Result<NamedStarter, &'static str> {
    let seed = bundled_seed(template)?;
    if expected_hash != seed_hash(template)? {
        return Err("Stale");
    }
    prepare_seed(seed, title, creation_id)
}

fn prepare_seed(
    mut seed: Seed,
    title: &str,
    creation_id: &str,
) -> Result<NamedStarter, &'static str> {
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
    let definition = definition(template)?;
    let seed = bundled_seed(template)?;
    let preview = StoryTemplatePreviewV1 {
        version: 1,
        template: template.into(),
        seed_sha256: seed_hash(template)?,
        default_title: definition.title.into(),
        description: definition.description.into(),
        profile: profile_name(&seed.profile).into(),
        details: player_details(&seed)?,
    };
    if serde_json::to_vec(&preview).map_err(|_| "Integrity")?.len() > 16384 {
        return Err("TooLarge");
    }
    Ok(preview)
}

fn configured_seed(template: &str, player_name: Option<&str>) -> Result<Seed, &'static str> {
    let mut seed = bundled_seed(template)?;
    if let Some(name) = player_name {
        if !valid_player_name(name) {
            return Err("InvalidInput");
        }
        let default_name = &seed.actors.get(&seed.player).ok_or("Integrity")?.name;
        if template == TEMPLATE && name != default_name {
            neutralize_lantern_player_references(&mut seed)?;
        }
        seed.actors.get_mut(&seed.player).ok_or("Integrity")?.name = name.into();
    }
    // The bundled default and every configured player must fit the same context boundary.
    if !valid_player_name(&seed.actors.get(&seed.player).ok_or("Integrity")?.name) {
        return Err("Integrity");
    }
    Engine::new(seed.clone()).map_err(|_| "Integrity")?;
    Ok(seed)
}

/// These two declared initial-seed subjects refer to the player, not an NPC
/// named by input text. Keep their content and epistemic ownership distinct;
/// never interpolate a player-controlled display name into facts or beliefs.
fn neutralize_lantern_player_references(seed: &mut Seed) -> Result<(), &'static str> {
    if seed.id != TEMPLATE
        || seed.player != "player"
        || seed
            .actors
            .get(&seed.player)
            .map(|actor| actor.name.as_str())
            != Some("Rowan")
    {
        return Err("Integrity");
    }
    let ancestry = seed.facts.get("ancestry").ok_or("Integrity")?;
    if ancestry.proposition != "Rowan was born to ordinary quay keepers."
        || ancestry.discoverable_at.is_some()
        || ancestry.known_by.len() != 1
        || !ancestry.known_by.contains("player")
    {
        return Err("Integrity");
    }
    let mut matches = seed.beliefs.iter().enumerate().filter(|(_, belief)| {
        belief.believer == "oren" && belief.source == Evidence::Seed(TEMPLATE.into())
    });
    let (index, belief) = matches.next().ok_or("Integrity")?;
    if matches.next().is_some()
        || belief.proposition != "Rowan may possess the tideglass relic."
        || belief.source_claim.is_some()
        || belief.confidence != Confidence::Suspected
    {
        return Err("Integrity");
    }
    // All declaration checks precede either replacement. Only fresh configured
    // seeds reach this helper; accepted history and default templates do not.
    seed.facts
        .get_mut("ancestry")
        .ok_or("Integrity")?
        .proposition = "The player was born to ordinary quay keepers.".into();
    seed.beliefs[index].proposition = "The player may possess the tideglass relic.".into();
    Ok(())
}

fn setup_hash(template_hash: &str, seed: &Seed) -> Result<String, &'static str> {
    let mut hash = Sha256::new();
    hash.update(b"locallore/player-setup/v1\0");
    hash.update(template_hash.as_bytes());
    hash.update(b"\0");
    hash.update(serde_json::to_vec(seed).map_err(|_| "Integrity")?);
    Ok(format!("{:x}", hash.finalize()))
}

/// A read-only initial setup with a player name and declared identity-neutral subjects.
pub fn setup_preview(
    template: &str,
    player_name: Option<&str>,
) -> Result<StorySetupPreviewV1, &'static str> {
    let definition = definition(template)?;
    let seed = configured_seed(template, player_name)?;
    let template_sha256 = seed_hash(template)?;
    let preview = StorySetupPreviewV1 {
        version: 1,
        template: template.into(),
        setup_sha256: setup_hash(&template_sha256, &seed)?,
        template_sha256,
        default_title: definition.title.into(),
        description: definition.description.into(),
        profile: profile_name(&seed.profile).into(),
        player_name: seed
            .actors
            .get(&seed.player)
            .ok_or("Integrity")?
            .name
            .clone(),
        details: player_details(&seed)?,
    };
    if serde_json::to_vec(&preview).map_err(|_| "Integrity")?.len() > 16384 {
        return Err("TooLarge");
    }
    Ok(preview)
}

pub fn prepare_configured(
    template: &str,
    template_sha256: &str,
    setup_sha256: &str,
    player_name: &str,
    title: &str,
    creation_id: &str,
) -> Result<NamedStarter, &'static str> {
    let seed = configured_seed(template, Some(player_name))?;
    let expected_template = seed_hash(template)?;
    let expected_setup = setup_hash(&expected_template, &seed)?;
    if template_sha256 != expected_template || setup_sha256 != expected_setup {
        return Err("Stale");
    }
    prepare_seed(seed, title, creation_id)
}

fn presentation_seed(
    template: &str,
    player_name: Option<&str>,
    presentation: Option<&crate::story_presentation::StoryPresentationV1>,
) -> Result<(Seed, crate::story_presentation::StoryPresentationV1), &'static str> {
    let mut seed = configured_seed(template, player_name)?;
    let presentation = presentation.cloned().unwrap_or_default();
    if !presentation.validate() {
        return Err("InvalidInput");
    }
    seed.presentation = (!presentation.is_default()).then(|| presentation.clone());
    Engine::new(seed.clone()).map_err(|_| "Integrity")?;
    Ok((seed, presentation))
}

fn presentation_hash(template_hash: &str, seed: &Seed) -> Result<String, &'static str> {
    let mut hash = Sha256::new();
    hash.update(b"locallore/story-presentation/v1\0");
    hash.update(template_hash.as_bytes());
    hash.update(b"\0");
    hash.update(serde_json::to_vec(seed).map_err(|_| "Integrity")?);
    Ok(format!("{:x}", hash.finalize()))
}

pub fn presentation_preview(
    template: &str,
    player_name: Option<&str>,
    presentation: Option<&crate::story_presentation::StoryPresentationV1>,
) -> Result<StoryPresentationPreviewV1, &'static str> {
    let definition = definition(template)?;
    let (seed, presentation) = presentation_seed(template, player_name, presentation)?;
    let template_sha256 = seed_hash(template)?;
    let mut details = player_details(&seed)?;
    if seed.presentation.is_some() {
        details.push(format!("Narration tone: {:?}", presentation.tone));
        details.extend(
            presentation
                .excluded_phrases
                .iter()
                .map(|phrase| format!("Phrase excluded from generated narration: {phrase}")),
        );
    }
    let preview = StoryPresentationPreviewV1 {
        version: 1,
        template: template.into(),
        setup_sha256: presentation_hash(&template_sha256, &seed)?,
        template_sha256,
        default_title: definition.title.into(),
        description: definition.description.into(),
        profile: profile_name(&seed.profile).into(),
        player_name: seed
            .actors
            .get(&seed.player)
            .ok_or("Integrity")?
            .name
            .clone(),
        presentation,
        details,
    };
    if preview.details.len() > 64
        || preview.details.iter().any(|row| row.len() > 2048)
        || serde_json::to_vec(&preview).map_err(|_| "Integrity")?.len() > 16384
    {
        return Err("TooLarge");
    }
    Ok(preview)
}

pub fn prepare_presented(
    template: &str,
    template_sha256: &str,
    setup_sha256: &str,
    player_name: &str,
    presentation: &crate::story_presentation::StoryPresentationV1,
    title: &str,
    creation_id: &str,
) -> Result<NamedStarter, &'static str> {
    let (seed, _) = presentation_seed(template, Some(player_name), Some(presentation))?;
    let expected_template = seed_hash(template)?;
    if template_sha256 != expected_template
        || setup_sha256 != presentation_hash(&expected_template, &seed)?
    {
        return Err("Stale");
    }
    prepare_seed(seed, title, creation_id)
}

fn player_details(seed: &Seed) -> Result<Vec<String>, &'static str> {
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
    if details.len() > 64 || details.iter().any(|line| line.len() > 2048) {
        return Err("TooLarge");
    }
    Ok(details)
}

#[cfg(test)]
mod reference_tests {
    use super::*;

    #[test]
    fn contradictory_template_reference_declarations_refuse_before_any_replacement() {
        for mutation in [
            "player",
            "default_name",
            "fact_text",
            "fact_known_by",
            "fact_discovery",
            "belief_missing",
            "belief_duplicate",
            "belief_text",
            "belief_source",
            "belief_claim",
            "belief_confidence",
        ] {
            let mut seed = bundled_seed(TEMPLATE).unwrap();
            let index = seed
                .beliefs
                .iter()
                .position(|belief| belief.believer == "oren")
                .unwrap();
            match mutation {
                "player" => seed.player = "mira".into(),
                "default_name" => {
                    seed.actors.get_mut("player").unwrap().name = "Changed template player".into()
                }
                "fact_text" => {
                    seed.facts.get_mut("ancestry").unwrap().proposition = "Changed ancestry".into()
                }
                "fact_known_by" => {
                    seed.facts
                        .get_mut("ancestry")
                        .unwrap()
                        .known_by
                        .insert("mira".into());
                }
                "fact_discovery" => {
                    seed.facts.get_mut("ancestry").unwrap().discoverable_at = Some("quay".into())
                }
                "belief_missing" => {
                    seed.beliefs.remove(index);
                }
                "belief_duplicate" => seed.beliefs.push(seed.beliefs[index].clone()),
                "belief_text" => seed.beliefs[index].proposition = "Changed belief".into(),
                "belief_source" => seed.beliefs[index].source = Evidence::Event(1),
                "belief_claim" => seed.beliefs[index].source_claim = Some(1),
                "belief_confidence" => seed.beliefs[index].confidence = Confidence::Believed,
                _ => unreachable!(),
            }
            let before = seed.clone();
            assert_eq!(
                neutralize_lantern_player_references(&mut seed),
                Err("Integrity"),
                "{mutation}"
            );
            assert_eq!(seed, before, "{mutation}");
        }
    }
}
