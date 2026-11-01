//! Player-only display projection over accepted native history. No inference or
//! caller-selected observer; legacy/thin snapshot contracts remain separate.
use crate::{contracts::*, engine::Engine};
use serde_json::{json, Value};
use std::collections::{BTreeMap, BTreeSet};

const DISPLAY_TURNS: usize = 20;

// This predicate consumes read-bound event identities, not purported accepted
// receipts. A single visible event cannot disclose a partly hidden whole turn.
fn whole_visible<'a>(
    identities: impl IntoIterator<Item = (&'a Scope, u64)>,
    eligible: &BTreeSet<(Scope, u64)>,
) -> bool {
    let mut any = false;
    for (scope, sequence) in identities {
        any = true;
        if !eligible.contains(&(scope.clone(), sequence)) {
            return false;
        }
    }
    any
}

// Android's JSON number reader cannot represent every native u64 exactly.
// Change only this display DTO: accepted Request/Receipt serialization stays
// numeric, while these two unsigned action fields use canonical decimal text.
fn intent_wire(intent: &Intent) -> Result<Value, Error> {
    let mut value = json!(intent);
    if let Intent::Actions(commands) = intent {
        let actions = value["value"].as_array_mut().ok_or(Error::CorruptHistory)?;
        if actions.len() != commands.len() {
            return Err(Error::CorruptHistory);
        }
        for (command, action) in commands.iter().zip(actions) {
            let (field, number) = match command {
                Command::Promise { deadline, .. } => ("deadline", *deadline),
                Command::Believe { claim_event } => ("claim_event", *claim_event),
                _ => continue,
            };
            *action.get_mut(field).ok_or(Error::CorruptHistory)? = json!(number.to_string());
        }
    }
    Ok(value)
}

pub(crate) fn project(engine: &Engine) -> Result<Value, Error> {
    let player = &engine.seed().player;
    // Reuse Core's current-scope/head/lineage/witness authority for both domains.
    // Neither the Host Story Lab grant nor a wire actor can widen this set.
    let eligible = engine
        .actor_receipts_v2(player, engine.scope(), engine.revision())?
        .into_iter()
        .flat_map(|receipt| receipt.events)
        .map(|event| (event.event.scope().clone(), event.event.sequence()))
        .collect::<BTreeSet<_>>();
    let visible = engine
        .canonical_records()
        .iter()
        .filter_map(|record| record.receipt())
        .filter(|receipt| {
            whole_visible(
                receipt
                    .events()
                    .iter()
                    .map(|event| (event.scope(), event.sequence())),
                &eligible,
            )
        })
        .collect::<Vec<_>>();
    let total = visible.len();
    if total > MAX_HISTORY_RECEIPTS {
        return Err(Error::TooLarge);
    }
    let start = total.saturating_sub(DISPLAY_TURNS);
    let mut turns = Vec::with_capacity(total - start);
    for receipt in &visible[start..] {
        if !matches!(
            receipt.request().intent,
            Intent::Actions(_) | Intent::Dialogue { .. } | Intent::FreeText { .. }
        ) {
            return Err(Error::CorruptHistory);
        }
        let event_ids = receipt
            .events()
            .iter()
            .map(AcceptedEvent::sequence)
            .collect::<Vec<_>>();
        if event_ids.first().is_none_or(|id| *id == 0)
            || event_ids.last().is_some_and(|id| *id > engine.revision())
            || event_ids.windows(2).any(|pair| pair[0] >= pair[1])
        {
            return Err(Error::CorruptHistory);
        }
        let intent = intent_wire(&receipt.request().intent)?;
        turns.push(json!({"original_scope":receipt.request().scope,"turn":receipt.request().turn,
            "event_ids":event_ids,"intent":intent,"narration":receipt.narration()}));
    }
    let state = engine.state();
    let self_state = state.actors.get(player).ok_or(Error::UnknownReference)?;
    let inventory = state
        .items
        .iter()
        .filter(|(_, item)| &item.owner == player)
        .collect::<BTreeMap<_, _>>();
    // Complete pairs and strings are preserved. Host/JNI retain their existing
    // independent reply caps and honestly reject an oversized fixed window.
    Ok(
        json!({"version":2,"domain_version":engine.domain_version(),"scope":engine.scope(),
        "revision":engine.revision(),"rules":engine.seed().profile,
        "player":{"observer":player,"self_state":self_state},"inventory":inventory,
        "turns":turns,"window":{"total":total,"start":start,"end":total}}),
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn whole_turn_requires_every_event_and_original_scope() {
        let main = Scope {
            story: "story".into(),
            branch: "main".into(),
        };
        let foreign = Scope {
            story: "other".into(),
            branch: "main".into(),
        };
        let eligible = [(main.clone(), 1), (main.clone(), 2)].into();
        assert!(whole_visible([(&main, 1), (&main, 2)], &eligible));
        assert!(!whole_visible([(&main, 1), (&main, 3)], &eligible));
        assert!(!whole_visible([(&foreign, 1)], &eligible));
    }

    #[test]
    fn empty_or_entirely_hidden_event_set_never_discloses_a_turn() {
        let scope = Scope {
            story: "story".into(),
            branch: "main".into(),
        };
        let eligible = BTreeSet::new();
        assert!(!whole_visible([], &eligible));
        assert!(!whole_visible([(&scope, 1)], &eligible));
    }
}
