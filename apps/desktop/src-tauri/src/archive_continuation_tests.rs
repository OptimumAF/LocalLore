// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen D08.06/M08.06 source, UNCOMPILED/UNRUN by its author.
//! Root registers as archive_v3_tests child:
//! #[path = "archive_continuation_tests.rs"] mod continuation_tests;
//! Coordinator command (Windows, existing owned native target/environment):
//! cargo test --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml archive::archive_v3_tests::continuation_tests:: -- --nocapture --test-threads=1
//! Actual native broker/filesystem + Repository/Host/Core/Store plumbing only;
//! scripted inference is synthetic, with no IPC/WebView/model/device claim.
//! No canonical writer, receipt deserializer, private Debug implementation,
//! provider metric fabrication, or new production bridge is introduced.
//! Frozen base abaa67eb2a836e192e30db92bb2e1782e3d2d62a;
//! claims #12 6392291771 / #30 6392291919. Registration belongs to Root.

use super::*;
use locallore::{
    contracts::{Error as CoreError, PlayInputKind, Request},
    host::Host,
    inference::{Cancellation, GenerationRequest, InferenceProvider, Input},
    play::PlayProfile,
};
use std::{sync::atomic::AtomicUsize, task::Poll};

#[derive(Clone, Default)]
struct ContinuationProbe {
    factories: Arc<AtomicUsize>,
    polls: Arc<AtomicUsize>,
    seen: Arc<Mutex<Vec<GenerationRequest>>>,
}

struct ContinuationScript {
    probe: ContinuationProbe,
    deny: bool,
}
impl InferenceProvider for ContinuationScript {
    fn poll(
        &mut self,
        request: &GenerationRequest,
        _: &Cancellation,
    ) -> Poll<std::result::Result<Vec<u8>, CoreError>> {
        let count = self.probe.polls.fetch_add(1, Ordering::SeqCst);
        if self.deny || count >= 2 {
            return Poll::Ready(Err(CoreError::Provider));
        }
        self.probe.seen.lock().unwrap().push(request.clone());
        let Input::Structured { role, .. } = &request.input else {
            return Poll::Ready(Err(CoreError::Provider));
        };
        let value = match role.as_str() {
            "director" => json!({"commands":[{"op":"wait","ticks":1}]}),
            "narrator" => {
                json!({"text":"Time passes.","event_ids":[request.revision+1],"speaker":"narrator"})
            }
            _ => return Poll::Ready(Err(CoreError::Provider)),
        };
        Poll::Ready(Ok(serde_json::to_vec(&value).unwrap()))
    }
}

fn continuation_profile() -> PlayProfile {
    PlayProfile {
        id: "synthetic-native-archive3-continuation".into(),
        model_sha256: "a".repeat(64),
        runtime_revision: "b".repeat(40),
        template_sha256: "c".repeat(64),
        worker_sha256: "d".repeat(64),
        profile_manifest_sha256: "e".repeat(64),
        context_tokens: 4096,
        director_tokens: 350,
        narrator_tokens: 220,
        deadline_ms: 5000,
        repair_limit: 1,
    }
}

fn configure_continuation(host: &Host, probe: &ContinuationProbe, deny: bool) {
    let probe = probe.clone();
    host.configure_fixture_provider(
        continuation_profile(),
        Arc::new(move || {
            probe.factories.fetch_add(1, Ordering::SeqCst);
            Box::new(ContinuationScript {
                probe: probe.clone(),
                deny,
            })
        }),
    )
    .unwrap();
}

fn host_call(host: &Host, command: Value) -> Value {
    host.call(&serde_json::to_vec(&json!({"version":1,"command":command})).unwrap())
}

fn host_data(reply: &Value) -> &Value {
    assert_eq!(reply["status"], "ok", "{reply}");
    &reply["data"]
}

fn host_resume(host: &Host, scope: &Scope) -> String {
    host_data(&host_call(host, json!({"op":"resume","scope":scope})))["session"]
        .as_str()
        .unwrap()
        .into()
}

fn host_control(host: &Host, session: &str, request: &Request, operation: &str) -> Value {
    host_call(
        host,
        json!({"op":operation,"session":session,"scope":request.scope,"turn":request.turn}),
    )
}

fn prior_history_and_privacy(continued: &Engine, fixture: &Fixture) {
    assert_eq!(continued.scope(), &fixture.active);
    assert_eq!(continued.domain_version(), 2);
    assert_eq!(continued.revision(), 4);
    assert_eq!(continued.canonical_record_count(), 4);
    assert_eq!(
        &continued.canonical_records()[..3],
        fixture.active_engine.canonical_records()
    );
    privacy(continued, &fixture.root, &fixture.corrected);
    for actor in ["player", "mira", "sable"] {
        let original = fixture
            .active_engine
            .actor_receipts_v2(actor, &fixture.active, 3)
            .unwrap();
        let current = continued
            .actor_receipts_v2(actor, &fixture.active, 4)
            .unwrap();
        for old in &original {
            let same_turn = current.iter().find(|view| view.turn == old.turn).unwrap();
            assert_eq!(same_turn, old);
        }
    }
}

#[test]
fn native_import_then_play25_wait_survives_cold_retry_without_repeating_generation_or_effects() {
    // Both an authored child and a live child of a physically retained retired
    // author parent must continue through the same public persistence bridge.
    for retired in [false, true] {
        let harness = Harness::new();
        let fixture = Fixture::new(&harness, retired);
        let source_database = fs::read(&fixture.path).unwrap();
        let (target, foreign, foreign_engine) = destination(&harness);
        let preview = harness.preview(&fixture.input);
        fixture.preview_shape(&preview["preview"]);
        let imported = harness.apply(&preview, &target);
        assert!(imported["error"].is_null(), "{imported}");
        assert_eq!(imported["result"]["status"], "imported");
        assert_eq!(imported["result"]["committed_turns"], 3);
        assert_eq!(imported["result"]["staging_cleanup_complete"], true);
        harness.clean_staging();
        fixture.preserved(&target, &foreign, &foreign_engine);

        let before = read(&target, &fixture.active);
        let request = before.request(
            "after-native-transfer-wait",
            Intent::FreeText {
                kind: PlayInputKind::Action,
                // Frozen comparison-suite Wait input, not retuned generation.
                text: "I wait for one tide tick.".into(),
            },
        );
        let host = locallore_workspace::open(&target, false).unwrap();
        let probe = ContinuationProbe::default();
        configure_continuation(&host, &probe, false);
        let session = host_resume(&host, &fixture.active);
        let queued = host_call(
            &host,
            json!({"op":"free_text","session":session,"request":request}),
        );
        assert_eq!(host_data(&queued)["phase"], "queued");
        equivalent(&read(&target, &fixture.active), &before);
        let ready = host_control(&host, &session, &request, "prepare");
        assert_eq!(host_data(&ready)["phase"], "ready");
        equivalent(&read(&target, &fixture.active), &before);
        let committed = host_control(&host, &session, &request, "commit");
        assert_eq!(host_data(&committed)["phase"], "committed");
        assert_eq!(probe.factories.load(Ordering::SeqCst), 1);
        assert_eq!(probe.polls.load(Ordering::SeqCst), 2);
        {
            let seen = probe.seen.lock().unwrap();
            assert_eq!(seen.len(), 2);
            for generated in seen.iter() {
                assert_eq!(generated.scope, fixture.active);
                assert_eq!(generated.turn, request.turn);
                assert_eq!(generated.revision, 3);
            }
        }
        drop(host);

        // Reopen actual committed bytes; no test receipt construction or decode.
        let mut store = Store::open_application(&target).unwrap();
        let saved = store.lookup_turn(&fixture.active, &request.turn).unwrap();
        assert_eq!(saved.phase, locallore_storage::TurnPhase::Committed);
        assert_eq!(saved.request, request);
        let receipt = saved.receipt.as_ref().unwrap();
        assert_eq!(receipt.request(), &request);
        assert_eq!(
            receipt.proposal().commands,
            vec![Command::Wait { ticks: 1 }]
        );
        assert_eq!(receipt.events().len(), 1);
        assert_eq!(receipt.events()[0].sequence(), 4);
        assert_eq!(receipt.events()[0].scope(), &fixture.active);
        let play = receipt.play().unwrap();
        assert_eq!(play.version, 2);
        assert_eq!(play.prompt_version, "locallore-play-v2.5");
        assert_eq!(play.profile, continuation_profile());
        let continued = store.resume(&fixture.active).unwrap().engine;
        prior_history_and_privacy(&continued, &fixture);
        equivalent(
            &store.resume(&fixture.root).unwrap().engine,
            &fixture.root_engine,
        );
        equivalent(&store.resume(&foreign).unwrap().engine, &foreign_engine);
        assert_eq!(store.stories().unwrap().len(), 2);
        if retired {
            assert!(matches!(
                store.resume(&fixture.corrected),
                Err(TurnError::Storage(StorageError::NotFound))
            ));
        }
        let continued_archive = store
            .export_archive(&fixture.root.story, &|| false)
            .unwrap();
        assert_eq!(continued_archive.preview().version, 3);
        assert_eq!(continued_archive.preview().committed_turns, 4);
        assert_ne!(continued_archive.bytes(), fixture.bytes.as_slice());
        assert_ne!(
            continued_archive.preview().payload_sha256,
            preview["preview"]["payload_sha256"].as_str().unwrap()
        );
        drop(store);

        // A fresh Repository/Host is intentionally configured to fail any
        // provider use. Recorded accepted outcomes must win without a factory.
        let reopened = locallore_workspace::open(&target, false).unwrap();
        let retry_probe = ContinuationProbe::default();
        configure_continuation(&reopened, &retry_probe, true);
        let session = host_resume(&reopened, &fixture.active);
        assert_eq!(
            host_call(
                &reopened,
                json!({"op":"free_text","session":session,"request":request})
            ),
            committed
        );
        for operation in ["prepare", "commit", "turn_status", "cancel"] {
            assert_eq!(
                host_control(&reopened, &session, &request, operation),
                committed
            );
        }
        let mut different = request.clone();
        let Intent::FreeText { text, .. } = &mut different.intent else {
            unreachable!()
        };
        text.push_str(" now");
        let mismatch = host_call(
            &reopened,
            json!({"op":"free_text","session":session,"request":different}),
        );
        assert_eq!(mismatch["status"], "rejected");
        assert_eq!(mismatch["error"], "RetryMismatch");
        assert_eq!(retry_probe.factories.load(Ordering::SeqCst), 0);
        assert_eq!(retry_probe.polls.load(Ordering::SeqCst), 0);
        assert!(retry_probe.seen.lock().unwrap().is_empty());
        drop(reopened);
        equivalent(&read(&target, &fixture.active), &continued);
        prior_history_and_privacy(&read(&target, &fixture.active), &fixture);
        equivalent(&read(&target, &fixture.root), &fixture.root_engine);
        equivalent(&read(&target, &foreign), &foreign_engine);
        equivalent(&read(&fixture.path, &fixture.root), &fixture.root_engine);
        equivalent(
            &read(&fixture.path, &fixture.active),
            &fixture.active_engine,
        );
        assert_eq!(fs::read(&fixture.path).unwrap(), source_database);
        assert_eq!(fs::read(&fixture.input).unwrap(), fixture.bytes);
        let cold_export = Store::open_read_only(&target)
            .unwrap()
            .export_archive(&fixture.root.story, &|| false)
            .unwrap();
        assert_eq!(cold_export.bytes(), continued_archive.bytes());
    }
}
