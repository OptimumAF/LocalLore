use locallore::{contracts::*, engine::Engine, memory_coverage::*};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::cell::Cell;

fn seed() -> Seed {
    serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap()
}
fn engine() -> Engine {
    Engine::new(seed()).unwrap()
}
fn commit(e: &mut Engine, turn: &str, commands: Vec<Command>) {
    let r = e.request(turn, Intent::Actions(commands));
    let p = Engine::proposal(&r).unwrap();
    let n = e.preview(&r, &p).unwrap().narration().to_owned();
    e.commit(&r, &p, &n).unwrap();
}
fn wait(e: &mut Engine, turn: &str) {
    commit(e, turn, vec![Command::Wait { ticks: 1 }]);
}
fn say(e: &mut Engine, turn: &str, text: &str) {
    commit(
        e,
        turn,
        vec![Command::Say {
            text: text.into(),
            audience: ["mira".into()].into(),
        }],
    );
}
fn request(e: &Engine, actor: &str) -> CoverageRequest {
    CoverageRequest {
        scope: e.scope().clone(),
        expected_head: e.revision(),
        observer: actor.into(),
    }
}
fn chunk(e: &Engine, actor: &str, after: u64) -> Option<TypedPacket> {
    build_chunk(
        e,
        &ChunkRequest {
            scope: e.scope().clone(),
            expected_head: e.revision(),
            observer: actor.into(),
            from_exclusive: after,
        },
        &|| false,
    )
    .unwrap()
}
fn all(e: &Engine, actor: &str) -> Vec<TypedPacket> {
    let mut result = vec![];
    let mut after = 0;
    while let Some(p) = chunk(e, actor, after) {
        assert!(p.through_revision > after);
        after = p.through_revision;
        result.push(p);
        assert!(result.len() <= MAX_PACKETS);
    }
    result
}
fn verify(e: &Engine, actor: &str, packets: &[TypedPacket]) -> VerifiedCoverage {
    let bytes = packets
        .iter()
        .map(|p| p.bytes().unwrap())
        .collect::<Vec<_>>();
    let borrowed = bytes.iter().map(Vec::as_slice).collect::<Vec<_>>();
    match verify_coverage(e, &request(e, actor), &borrowed, &|| false).unwrap() {
        CoverageRead::Verified(v) => v,
        CoverageRead::RawFallback(reason) => panic!("unexpected fallback {reason:?}"),
    }
}
fn fallback(e: &Engine, actor: &str, values: &[Value]) -> FallbackReason {
    let bytes = values
        .iter()
        .map(|p| serde_json::to_vec(p).unwrap())
        .collect::<Vec<_>>();
    let borrowed = bytes.iter().map(Vec::as_slice).collect::<Vec<_>>();
    match verify_coverage(e, &request(e, actor), &borrowed, &|| false).unwrap() {
        CoverageRead::RawFallback(reason) => reason,
        CoverageRead::Verified(_) => panic!("untrusted modification was accepted"),
    }
}

#[test]
fn thousand_event_history_has_exact_complete_scoped_coverage_and_typed_origins() {
    let mut e = engine();
    commit(
        &mut e,
        "old-promise",
        vec![Command::Promise {
            id: "old-promise".into(),
            to: "mira".into(),
            terms: "Repair the beacon after distractions".into(),
            deadline: 5000,
            return_item: None,
        }],
    );
    say(
        &mut e,
        "claim",
        "The relic is in old-ruins: CLAIM-NOT-TRUTH",
    );
    commit(&mut e, "belief", vec![Command::Believe { claim_event: 2 }]);
    for i in 0..1025 {
        wait(&mut e, &format!("distractor-{i}"));
    }
    let before = e.canonical_bytes();
    let receipts = e.receipts().to_vec();
    let packets = all(&e, "player");
    assert!(packets.len() > 1);
    let v = verify(&e, "player", &packets);
    assert_eq!(v.covered_through(), e.revision());
    assert_eq!(v.raw_delta_after(), e.revision());
    let actual: Vec<_> = packets
        .iter()
        .flat_map(|p| p.source_events.clone())
        .collect();
    let wanted: Vec<_> = e
        .character_context("player", e.scope(), e.revision())
        .unwrap()
        .observations
        .iter()
        .map(|event| SourceRef {
            scope: event.scope().clone(),
            sequence: event.sequence(),
        })
        .collect();
    assert_eq!(actual, wanted);
    assert!(matches!(
        packets[0].entries[0],
        Entry::Observation {
            origin: ObservationClass::CanonicalObservation,
            ..
        }
    ));
    assert!(matches!(
        packets[0].entries[1],
        Entry::Observation {
            origin: ObservationClass::Statement,
            ..
        }
    ));
    assert!(matches!(
        packets[0].entries[2],
        Entry::Observation {
            origin: ObservationClass::Belief,
            ..
        }
    ));
    for p in &packets {
        assert!(p.bytes().unwrap().len() <= MAX_PACKET_BYTES);
        assert!(p.receipt_count <= MAX_RECEIPTS);
        assert!(p.source_events.len() <= MAX_EVENTS);
    }
    assert_eq!(before, e.canonical_bytes());
    assert_eq!(receipts, e.receipts());
    assert_eq!(packets, all(&e, "player"));
}

#[test]
fn eligibility_precedes_entries_even_for_empty_hidden_windows_and_private_seed_text() {
    let mut e = engine();
    say(&mut e, "secret", "PRIVATE-MIRA-ONLY-CANARY");
    for i in 0..128 {
        wait(&mut e, &format!("hidden-time-{i}"));
    }
    let mira = all(&e, "mira");
    let sable = all(&e, "sable");
    assert!(String::from_utf8(mira[0].bytes().unwrap())
        .unwrap()
        .contains("PRIVATE-MIRA-ONLY-CANARY"));
    assert_eq!(sable[0].closure, Closure::ReceiptLimit);
    assert_eq!(sable[0].through_revision, 128);
    assert!(sable
        .iter()
        .all(|p| p.entries.is_empty() && p.source_events.is_empty()));
    let raw = serde_json::to_string(&sable).unwrap();
    for secret in ["PRIVATE-MIRA-ONLY-CANARY", "SECRET-TIDE-731", "old-ruins"] {
        assert!(!raw.contains(secret));
    }
    assert_eq!(verify(&e, "sable", &sable).covered_through(), 129);
    let invalid = ChunkRequest {
        scope: e.scope().clone(),
        expected_head: e.revision(),
        observer: "missing".into(),
        from_exclusive: 0,
    };
    assert_eq!(
        build_chunk(&e, &invalid, &|| false),
        Err(CoverageError::Observer)
    );
}

#[test]
fn nested_prebirth_lineage_preserves_original_scopes_and_rejects_same_scope_other_ancestry() {
    let mut root = engine();
    say(&mut root, "inherited", "INHERITED-CANARY");
    for i in 0..4 {
        say(&mut root, &format!("future-{i}"), "PARENT-FUTURE-CANARY");
    }
    let a = root.fork("a", 5).unwrap();
    let mut b = a.fork("b", 1).unwrap();
    say(&mut b, "local", "B-LOCAL-CANARY");
    let mut sibling = root.fork("sibling", 1).unwrap();
    say(&mut sibling, "local", "SIBLING-CANARY");
    let packets = all(&b, "mira");
    let v = verify(&b, "mira", &packets);
    assert_eq!(
        packets[0]
            .source_events
            .iter()
            .map(|s| (s.scope.branch.as_str(), s.sequence))
            .collect::<Vec<_>>(),
        [("main", 1), ("b", 2)]
    );
    let raw = String::from_utf8(packets[0].bytes().unwrap()).unwrap();
    assert!(raw.contains("INHERITED-CANARY") && raw.contains("B-LOCAL-CANARY"));
    assert!(!raw.contains("PARENT-FUTURE-CANARY") && !raw.contains("SIBLING-CANARY"));
    say(&mut root, "further-parent", "IGNORED-PARENT-FUTURE");
    assert!(matches!(
        v.recheck(&b, &request(&b, "mira"), &|| false).unwrap(),
        CoverageRead::Verified(_)
    ));
    let mut direct = root.fork("b", 1).unwrap();
    say(&mut direct, "local", "B-LOCAL-CANARY");
    assert_eq!(direct.receipts(), b.receipts());
    assert_eq!(direct.canonical_bytes(), b.canonical_bytes());
    assert_eq!(
        fallback(
            &direct,
            "mira",
            &[serde_json::to_value(&packets[0]).unwrap()]
        ),
        FallbackReason::Binding
    );
    assert_eq!(
        fallback(
            &sibling,
            "mira",
            &[serde_json::to_value(&packets[0]).unwrap()]
        ),
        FallbackReason::Binding
    );
}

#[test]
fn old_open_tail_remains_verified_prefix_and_exact_delta_is_never_claimed_covered() {
    let mut e = engine();
    wait(&mut e, "first");
    let old = all(&e, "player");
    assert_eq!(old[0].closure, Closure::OpenTail);
    let v = verify(&e, "player", &old);
    commit(
        &mut e,
        "gift",
        vec![Command::Give {
            item: "potion".into(),
            to: "mira".into(),
            quantity: 1,
        }],
    );
    let newer = match v.recheck(&e, &request(&e, "player"), &|| false).unwrap() {
        CoverageRead::Verified(v) => v,
        _ => panic!("old prefix is unchanged"),
    };
    assert_eq!(newer.verified_head(), 2);
    assert_eq!(newer.raw_delta_after(), 1);
    assert!(newer
        .packets()
        .iter()
        .flat_map(|p| &p.source_events)
        .all(|s| s.sequence <= 1));
    assert_eq!(
        e.state().items["potion"].owner,
        "mira",
        "current canonical facts remain in Engine, never inferred from old packet"
    );
    let rebuilt = chunk(&e, "player", 0).unwrap();
    assert_eq!(rebuilt.from_exclusive, old[0].from_exclusive);
    assert_eq!(rebuilt.through_revision, 2);
    assert_ne!(rebuilt.source_sha256, old[0].source_sha256);
    let mut changed = seed();
    changed.facts.get_mut("ancestry").unwrap().proposition = "A different canonical seed".into();
    let mut other = Engine::new(changed).unwrap();
    wait(&mut other, "first");
    assert_eq!(
        fallback(&other, "player", &[serde_json::to_value(&old[0]).unwrap()]),
        FallbackReason::Binding
    );
}

#[test]
fn tail_replacement_does_not_append_one_cache_slot_per_commit() {
    let mut e = engine();
    for i in 0..150 {
        wait(&mut e, &format!("turn-{i}"));
        let packets = all(&e, "player");
        assert!(packets.len() <= 2);
        assert_eq!(packets[0].from_exclusive, 0);
        if i < 127 {
            assert_eq!(packets[0].closure, Closure::OpenTail);
        } else {
            assert_eq!(packets[0].closure, Closure::ReceiptLimit);
        }
        assert_eq!(
            verify(&e, "player", &packets).covered_through(),
            e.revision()
        );
    }
}

#[test]
fn complete_turn_event_overflow_requires_actual_lookahead_and_never_splits_a_turn() {
    let mut e = engine();
    for i in 0..37 {
        commit(
            &mut e,
            &format!("seven-{i}"),
            vec![Command::Wait { ticks: 1 }; 7],
        );
    }
    let p = chunk(&e, "player", 0).unwrap();
    assert_eq!(p.source_events.len(), 252);
    assert_eq!(p.receipt_count, 36);
    assert_eq!(p.through_revision, 252);
    assert_eq!(p.closure, Closure::EventBudget { next_turn_end: 259 });
    assert_eq!(
        verify(&e, "player", std::slice::from_ref(&p)).covered_through(),
        252
    );
    let historical = e.at_revision(252).unwrap();
    assert_eq!(
        fallback(&historical, "player", &[serde_json::to_value(&p).unwrap()]),
        FallbackReason::UnprovableClosure
    );
    let q = ChunkRequest {
        scope: e.scope().clone(),
        expected_head: e.revision(),
        observer: "player".into(),
        from_exclusive: 1,
    };
    assert_eq!(build_chunk(&e, &q, &|| false), Err(CoverageError::Boundary));
}

#[test]
fn encoded_budget_closure_is_recomputed_and_cannot_be_forged_from_eof() {
    let mut e = engine();
    for i in 0..40 {
        say(&mut e, &format!("speech-{i}"), &"X".repeat(MAX_TEXT_BYTES));
    }
    let p = chunk(&e, "mira", 0).unwrap();
    assert!(
        matches!(p.closure, Closure::PacketBudget { next_turn_end } if next_turn_end == p.through_revision + 1)
    );
    assert!(p.bytes().unwrap().len() <= MAX_PACKET_BYTES);
    verify(&e, "mira", std::slice::from_ref(&p));
    let before_lookahead = e.at_revision(p.through_revision).unwrap();
    assert_eq!(
        fallback(
            &before_lookahead,
            "mira",
            &[serde_json::to_value(&p).unwrap()]
        ),
        FallbackReason::UnprovableClosure
    );
    let mut one = engine();
    wait(&mut one, "one");
    let mut forged = serde_json::to_value(chunk(&one, "player", 0).unwrap()).unwrap();
    forged["closure"] = json!({"kind":"receipt_limit"});
    assert_eq!(
        fallback(&one, "player", &[forged]),
        FallbackReason::SourceMismatch
    );
}

#[test]
fn hostile_cache_sets_never_certify_gaps_duplicates_omissions_additions_or_changed_content() {
    let mut e = engine();
    say(&mut e, "first", "ACTUAL-TEXT");
    for i in 0..130 {
        wait(&mut e, &format!("time-{i}"));
    }
    let p = all(&e, "mira");
    let a = serde_json::to_value(&p[0]).unwrap();
    let b = serde_json::to_value(&p[1]).unwrap();
    assert_eq!(
        fallback(&e, "mira", std::slice::from_ref(&b)),
        FallbackReason::Gap
    );
    assert_eq!(
        fallback(&e, "mira", &[a.clone(), a.clone()]),
        FallbackReason::Overlap
    );
    let mut gap = b.clone();
    gap["from_exclusive"] = json!(129);
    assert_eq!(fallback(&e, "mira", &[a.clone(), gap]), FallbackReason::Gap);
    let mut unknown = a.clone();
    unknown["extra"] = json!(true);
    assert_eq!(fallback(&e, "mira", &[unknown]), FallbackReason::Malformed);
    let mut future = a.clone();
    future["version"] = json!(3);
    assert_eq!(fallback(&e, "mira", &[future]), FallbackReason::Unsupported);
    for change in 0..5 {
        let mut bad = a.clone();
        match change {
            0 => {
                bad["source_events"].as_array_mut().unwrap().pop();
            }
            1 => {
                let copied = bad["source_events"][0].clone();
                bad["source_events"].as_array_mut().unwrap().push(copied);
            }
            2 => bad["entries"][0]["event"]["outcome"]["text"] = json!("FORGED-HIDDEN-CANARY"),
            3 => bad["source_events"][0]["scope"]["branch"] = json!("sibling"),
            _ => bad["source_sha256"] = json!("f".repeat(64)),
        }
        assert_eq!(fallback(&e, "mira", &[bad]), FallbackReason::SourceMismatch);
    }
    let mut one = engine();
    wait(&mut one, "one");
    let open = serde_json::to_value(chunk(&one, "mira", 0).unwrap()).unwrap();
    assert_eq!(
        fallback(&e, "mira", &[open, b]),
        FallbackReason::OpenTailBeforeEnd
    );
    let bytes = p[0].bytes().unwrap();
    let duplicate = String::from_utf8(bytes).unwrap().replacen(
        "\"version\":2",
        "\"version\":2,\"version\":2",
        1,
    );
    assert!(matches!(
        verify_coverage(&e, &request(&e, "mira"), &[duplicate.as_bytes()], &|| false).unwrap(),
        CoverageRead::RawFallback(FallbackReason::Malformed)
    ));
    assert!(matches!(
        verify_coverage(&e, &request(&e, "mira"), &[], &|| false).unwrap(),
        CoverageRead::RawFallback(FallbackReason::Missing)
    ));
}

#[test]
fn cancellation_and_wrong_live_bindings_fail_closed_without_partial_results_or_mutation() {
    let mut e = engine();
    say(&mut e, "one", "ACTUAL");
    wait(&mut e, "two");
    let q = ChunkRequest {
        scope: e.scope().clone(),
        expected_head: e.revision(),
        observer: "mira".into(),
        from_exclusive: 0,
    };
    let before = e.canonical_bytes();
    let receipts = e.receipts().to_vec();
    let total = Cell::new(0);
    build_chunk(&e, &q, &|| {
        total.set(total.get() + 1);
        false
    })
    .unwrap();
    for stop in 1..=total.get() {
        let count = Cell::new(0);
        assert_eq!(
            build_chunk(&e, &q, &|| {
                count.set(count.get() + 1);
                count.get() == stop
            }),
            Err(CoverageError::Cancelled)
        );
    }
    let p = all(&e, "mira");
    let bytes = p[0].bytes().unwrap();
    let total = Cell::new(0);
    verify_coverage(&e, &request(&e, "mira"), &[&bytes], &|| {
        total.set(total.get() + 1);
        false
    })
    .unwrap();
    for stop in 1..=total.get() {
        let count = Cell::new(0);
        assert!(matches!(
            verify_coverage(&e, &request(&e, "mira"), &[&bytes], &|| {
                count.set(count.get() + 1);
                count.get() == stop
            }),
            Err(CoverageError::Cancelled)
        ));
    }
    assert!(matches!(
        verify_coverage(&e, &request(&e, "mira"), &[&bytes], &|| panic!(
            "synthetic cancelled callback"
        )),
        Err(CoverageError::Cancelled)
    ));
    let mut stale = request(&e, "mira");
    stale.expected_head = 0;
    assert!(matches!(
        verify_coverage(&e, &stale, &[&bytes], &|| false),
        Err(CoverageError::Stale)
    ));
    stale = request(&e, "mira");
    stale.scope.story = "foreign".into();
    assert!(matches!(
        verify_coverage(&e, &stale, &[&bytes], &|| false),
        Err(CoverageError::Scope)
    ));
    assert_eq!(before, e.canonical_bytes());
    assert_eq!(receipts, e.receipts());
    assert!(chunk(&engine(), "player", 0).is_none());
}

#[test]
fn public_caps_hold_across_wide_scopes_and_exact_event_quantum_without_lookahead() {
    for width in [1, 32, 64] {
        let mut seed = seed();
        seed.scope.story = "s".repeat(width);
        seed.scope.branch = "b".repeat(width);
        let mut e = Engine::new(seed).unwrap();
        for i in 0..34 {
            commit(
                &mut e,
                &format!("many-{i}"),
                vec![Command::Wait { ticks: 1 }; 8],
            );
        }
        for actor in ["player", "mira", "sable"] {
            let packets = all(&e, actor);
            let v = verify(&e, actor, &packets);
            assert_eq!(v.covered_through(), e.revision());
            for p in packets {
                assert!(p.receipt_count <= MAX_RECEIPTS);
                assert!(p.source_events.len() <= MAX_EVENTS);
                assert!(p.bytes().unwrap().len() <= MAX_PACKET_BYTES);
                let bytes: usize = e
                    .character_context(actor, e.scope(), e.revision())
                    .unwrap()
                    .observations
                    .iter()
                    .filter(|event| {
                        event.sequence() > p.from_exclusive
                            && event.sequence() <= p.through_revision
                    })
                    .map(|event| serde_json::to_vec(event).unwrap().len())
                    .sum();
                assert!(bytes <= MAX_SOURCE_BYTES);
            }
        }
        if width == 1 {
            let packet = chunk(&e, "player", 0).unwrap();
            assert_eq!(packet.closure, Closure::EventLimit);
            assert_eq!(packet.through_revision, 256);
            let historical = e.at_revision(256).unwrap();
            verify(&historical, "player", &[packet]);
        }
    }
}

#[test]
fn recomputing_digest_of_forged_event_does_not_turn_checksum_into_history_authority() {
    let mut e = engine();
    say(&mut e, "one", "ACTUAL-TEXT");
    let p = chunk(&e, "mira", 0).unwrap();
    let mut forged = serde_json::to_value(&p).unwrap();
    forged["entries"][0]["event"]["outcome"]["text"] = json!("FORGED-TEXT");
    // Independently recompute the specified v2 digest for the forged source bytes,
    // preserving the event's original typed JSON key order. This is not a signature.
    let raw = serde_json::to_string(&e.receipts()[0].events()[0])
        .unwrap()
        .replace("ACTUAL-TEXT", "FORGED-TEXT");
    let domain = serde_json::to_vec(&(
        &p.scope,
        &p.observer,
        &p.seed_sha256,
        &p.lineage_sha256,
        p.from_exclusive,
    ))
    .unwrap();
    let mut digest = Sha256::new();
    digest.update(b"locallore-memory-coverage-v2\0");
    digest.update((domain.len() as u64).to_le_bytes());
    digest.update(domain);
    digest.update((raw.len() as u64).to_le_bytes());
    digest.update(raw.as_bytes());
    digest.update(p.through_revision.to_le_bytes());
    let rehashed = format!("{:x}", digest.finalize());
    assert_ne!(rehashed, p.source_sha256);
    forged["source_sha256"] = json!(rehashed);
    assert_eq!(
        fallback(&e, "mira", &[forged]),
        FallbackReason::SourceMismatch
    );
    assert_eq!(verify(&e, "mira", &[p]).covered_through(), 1);
}

#[test]
fn public_packet_encoding_and_untrusted_input_are_bounded_before_materialization() {
    let mut e = engine();
    wait(&mut e, "one");
    let mut p = chunk(&e, "player", 0).unwrap();
    p.method = "\0".repeat(MAX_PACKET_BYTES / 2);
    assert_eq!(
        p.bytes(),
        Err(CoverageError::Budget),
        "JSON escaping stops the bounded encoder"
    );
    let oversized = vec![b' '; MAX_PACKET_BYTES + 1];
    assert!(matches!(
        verify_coverage(&e, &request(&e, "player"), &[&oversized], &|| false).unwrap(),
        CoverageRead::RawFallback(FallbackReason::Budget)
    ));
    let normal = chunk(&e, "player", 0).unwrap().bytes().unwrap();
    let too_many = vec![normal.as_slice(); MAX_PACKETS + 1];
    assert!(matches!(
        verify_coverage(&e, &request(&e, "player"), &too_many, &|| false).unwrap(),
        CoverageRead::RawFallback(FallbackReason::Budget)
    ));
}

#[test]
fn first_wait_packet_freezes_v2_wire_identity_separately_from_reduced_budget_test() {
    let mut e = engine();
    wait(&mut e, "one");
    let p = chunk(&e, "player", 0).unwrap();
    assert_eq!(p.version, 2);
    assert_eq!(p.receipt_count, 1);
    assert_eq!(p.closure, Closure::OpenTail);
    assert!(
        matches!(&p.entries[..], [Entry::ObservedTimeSpan { from: 100, to: 101, source_events }] if source_events == &p.source_events)
    );
    let digest = format!("{:x}", Sha256::digest(p.bytes().unwrap()));
    assert_eq!(
        digest,
        "37c1b6bbc85f4442a24c8325cea02def28d29e540e76186e3f325a43dd0c1f97"
    );
}
