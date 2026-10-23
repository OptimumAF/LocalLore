//! Independent adversarial coverage checks using actual canonical Engine commits.
use locallore::{contracts::*, engine::Engine, memory_coverage::*};

fn engine() -> Engine {
    Engine::new(serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap())
        .unwrap()
}
fn commit(engine: &mut Engine, turn: &str, command: Command) {
    let request = engine.request(turn, Intent::Actions(vec![command]));
    let proposal = Engine::proposal(&request).unwrap();
    let narration = engine
        .preview(&request, &proposal)
        .unwrap()
        .narration()
        .to_owned();
    engine.commit(&request, &proposal, &narration).unwrap();
}
fn request(engine: &Engine, observer: &str) -> CoverageRequest {
    CoverageRequest {
        scope: engine.scope().clone(),
        expected_head: engine.revision(),
        observer: observer.into(),
    }
}
fn first(engine: &Engine, observer: &str) -> TypedPacket {
    build_chunk(
        engine,
        &ChunkRequest {
            scope: engine.scope().clone(),
            expected_head: engine.revision(),
            observer: observer.into(),
            from_exclusive: 0,
        },
        &|| false,
    )
    .unwrap()
    .unwrap()
}
fn verified(engine: &Engine, observer: &str, packet: &TypedPacket) -> VerifiedCoverage {
    let bytes = packet.bytes().unwrap();
    match verify_coverage(engine, &request(engine, observer), &[&bytes], &|| false).unwrap() {
        CoverageRead::Verified(verified) => verified,
        CoverageRead::RawFallback(reason) => panic!("unexpected raw fallback: {reason:?}"),
    }
}

#[test]
fn retained_opaque_coverage_rechecks_actual_history_when_all_binding_headers_match() {
    let mut original = engine();
    let mut alternate = engine();
    for (engine, text) in [
        (&mut original, "ORIGINAL-ACCEPTED-STATEMENT"),
        (&mut alternate, "DIFFERENT-ACCEPTED-STATEMENT"),
    ] {
        commit(
            engine,
            "same-turn-key",
            Command::Say {
                text: text.into(),
                audience: ["mira".into()].into(),
            },
        );
    }
    let packet = first(&original, "mira");
    let alternate_packet = first(&alternate, "mira");
    assert_eq!(packet.scope, alternate_packet.scope);
    assert_eq!(packet.observer, alternate_packet.observer);
    assert_eq!(packet.seed_sha256, alternate_packet.seed_sha256);
    assert_eq!(packet.lineage_sha256, alternate_packet.lineage_sha256);
    assert_eq!(packet.through_revision, alternate_packet.through_revision);
    assert_eq!(packet.source_events, alternate_packet.source_events);
    assert_ne!(packet.source_sha256, alternate_packet.source_sha256);
    let retained = verified(&original, "mira", &packet);
    let before = alternate.canonical_bytes();
    let receipts = alternate.receipts().to_vec();
    assert!(matches!(
        retained
            .recheck(&alternate, &request(&alternate, "mira"), &|| false)
            .unwrap(),
        CoverageRead::RawFallback(FallbackReason::SourceMismatch)
    ));
    assert_eq!(alternate.canonical_bytes(), before);
    assert_eq!(alternate.receipts(), receipts);
    assert!(matches!(
        retained
            .recheck(&original, &request(&original, "mira"), &|| false)
            .unwrap(),
        CoverageRead::Verified(_)
    ));
}

#[test]
fn entirely_hidden_sealed_prefix_remains_coverage_only_of_its_original_boundary() {
    let mut engine = engine();
    for index in 0..129 {
        commit(
            &mut engine,
            &format!("hidden-{index}"),
            Command::Wait { ticks: 1 },
        );
    }
    let packet = first(&engine, "sable");
    assert_eq!(packet.closure, Closure::ReceiptLimit);
    assert_eq!(packet.through_revision, 128);
    assert_eq!(packet.receipt_count, 128);
    assert!(packet.entries.is_empty() && packet.source_events.is_empty());
    let retained = verified(&engine, "sable", &packet);
    commit(&mut engine, "later-hidden", Command::Wait { ticks: 1 });
    let before = engine.canonical_bytes();
    let checked = match retained
        .recheck(&engine, &request(&engine, "sable"), &|| false)
        .unwrap()
    {
        CoverageRead::Verified(checked) => checked,
        CoverageRead::RawFallback(reason) => panic!("unexpected raw fallback: {reason:?}"),
    };
    assert_eq!(checked.verified_head(), 130);
    assert_eq!(checked.covered_through(), 128);
    assert_eq!(checked.raw_delta_after(), 128);
    assert!(checked.packets()[0].entries.is_empty());
    assert_eq!(engine.canonical_bytes(), before);
}

#[test]
fn real_escaped_unicode_statements_close_by_encoded_packet_budget_and_roundtrip_exactly() {
    let mut engine = engine();
    let speech = "\"\\\n\tÉ".repeat(160);
    assert!(speech.len() <= MAX_TEXT_BYTES);
    for index in 0..40 {
        commit(
            &mut engine,
            &format!("escaped-{index}"),
            Command::Say {
                text: speech.clone(),
                audience: ["mira".into()].into(),
            },
        );
    }
    let before = engine.canonical_bytes();
    let packet = first(&engine, "mira");
    assert!(matches!(packet.closure, Closure::PacketBudget { .. }));
    assert!(packet.through_revision < engine.revision());
    let encoded = packet.bytes().unwrap();
    assert!(encoded.len() <= MAX_PACKET_BYTES);
    let checked = verified(&engine, "mira", &packet);
    assert_eq!(checked.covered_through(), packet.through_revision);
    let value = serde_json::from_slice::<serde_json::Value>(&encoded).unwrap();
    assert_eq!(value["entries"][0]["event"]["outcome"]["text"], speech);
    let hidden = first(&engine, "sable");
    assert!(hidden.entries.is_empty() && hidden.source_events.is_empty());
    assert_eq!(hidden.through_revision, engine.revision());
    assert_eq!(engine.canonical_bytes(), before);
}
