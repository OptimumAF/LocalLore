// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Fixed pre-factoring compiler-byte oracle. References captured on unchanged
//! Core41fa2fad before production changes; no environment/update hook.
use locallore::{
    context_compiler::{
        compile_policy_cancelled, Budget, CompileRequest, ContextPolicy, Payload,
        PolicyCompilation, Role, POLICY_COMPILER_VERSION,
    },
    contracts::{Command, Intent},
    engine::{render, Engine},
};
use sha2::{Digest, Sha256};

const BASE: &str = "41fa2fad4c17345657c115b946e9472b1abd93cb";
const UNICODE: &str =
    "Mira, keep the harbor promise: café 灯 🧭; \"quoted\" \\ tide.\nSecond line.";
const PRIVATE: &str = "PRIVATE_TYPED_GOLDEN_PLAYER_ONLY";
const EXPECTED: [(&str, &str); 6] = [
    (
        "main-player-recent",
        "550f8503e5d71fb2bf5543698877dcc551c6fd6a59f6cba0ac4bf81c8e41878f",
    ),
    (
        "main-player-relevant",
        "25a97d1e671848b54c5568743d1f79c7d776a62e659f21bcf2d01408db36dac9",
    ),
    (
        "main-mira-recent",
        "80c571c274e95cc37898ad05507ea4e8d5a7a172135c82a72982d71721967713",
    ),
    (
        "main-mira-relevant",
        "cf593b39acbc0066f0337c370530cffb686a60ffa0b06c18670c23387f14fb7e",
    ),
    (
        "fork-player-recent",
        "29cfefee5b84662253acc55ee7773d4519eac110b04fdf3564509fbfda76e62d",
    ),
    (
        "fork-player-relevant",
        "bc70cd8c8e253b8798f133f057fe0e842002070da284480620f04e5e73d38209",
    ),
];

fn say(text: &str, audience: &str) -> Command {
    Command::Say {
        text: text.into(),
        audience: [audience.into()].into(),
    }
}
fn commit(engine: &mut Engine, key: &str, intent: Intent) {
    let request = engine.request(key, intent);
    let proposal = Engine::proposal(&request).unwrap();
    let preview = engine.preview(&request, &proposal).unwrap();
    assert_eq!(preview.narration(), render(preview.events()));
    let receipt = engine
        .commit(&request, &proposal, preview.narration())
        .unwrap();
    assert_eq!(
        receipt, preview,
        "actual accepted receipt, not handcrafted history"
    );
}
fn fixture() -> (Engine, Engine) {
    let mut main = Engine::new(
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap(),
    )
    .unwrap();
    commit(
        &mut main,
        "typed-unit",
        Intent::Actions(vec![
            say("The harbor promise remains witnessed.", "mira"),
            say(PRIVATE, "player"),
        ]),
    );
    assert_eq!(main.revision(), 2);
    commit(
        &mut main,
        "unicode-dialogue",
        Intent::Dialogue {
            text: UNICODE.into(),
            audience: ["mira".into()].into(),
        },
    );
    commit(
        &mut main,
        "private-only",
        Intent::Actions(vec![say("PRIVATE_EMPTY_NPC_UNIT", "player")]),
    );
    assert_eq!(main.revision(), 4);
    let mut child = main.fork("literal-golden", 2).unwrap();
    // Same bare turn as its inherited typed receipt, different actual scope.
    // Parent future dialogue/private receipt must never become child history.
    commit(
        &mut child,
        "typed-unit",
        Intent::Dialogue {
            text: "Child harbor conversation: déjà vu 灯.".into(),
            audience: ["mira".into()].into(),
        },
    );
    assert_eq!(child.revision(), 3);
    (main, child)
}
fn compile(engine: &Engine, observer: &str, policy: ContextPolicy) -> PolicyCompilation {
    compile_policy_cancelled(
        engine,
        &CompileRequest {
            version: POLICY_COMPILER_VERSION,
            scope: engine.scope().clone(),
            expected_head: engine.revision(),
            at_revision: None,
            observer: observer.into(),
            role: if observer == "player" {
                Role::Director
            } else {
                Role::Character
            },
            query: "harbor".into(),
            referenced_ids: vec![],
            budget: Budget {
                recent_events: 0,
                optional_records: 6,
                ..Budget::default()
            },
        },
        policy,
        None,
        &|| false,
    )
    .unwrap()
}

#[test]
fn full_policy_compilation_bytes_preserve_existing_transcript_payloads_and_diagnostics() {
    let (main, child) = fixture();
    let policies = [
        ContextPolicy::StateRecentTranscriptV1,
        ContextPolicy::StateRelevantMemoryV1,
    ];
    let cases = [
        (&main, "player", policies[0]),
        (&main, "player", policies[1]),
        (&main, "mira", policies[0]),
        (&main, "mira", policies[1]),
        (&child, "player", policies[0]),
        (&child, "player", policies[1]),
    ];
    let mut observed = Vec::new();
    for ((engine, observer, policy), (name, _)) in cases.into_iter().zip(EXPECTED) {
        let value = compile(engine, observer, policy);
        // Hash the ENTIRE current DTO: package, coverage, selection diagnostics
        // and policy construction diagnostics, not a handpicked projection.
        let bytes = serde_json::to_vec(&value).unwrap();
        let sha256 = format!("{:x}", Sha256::digest(&bytes));
        eprintln!(
            "LEGACY_POLICY_BYTES base={BASE} case={name} bytes={} sha256={sha256}",
            bytes.len()
        );
        observed.push((name, sha256));
        if observer == "mira" {
            let text = std::str::from_utf8(&bytes).unwrap();
            assert!(!text.contains(PRIVATE));
            assert!(!text.contains("PRIVATE_EMPTY_NPC_UNIT"));
        }
        if policy == ContextPolicy::StateRecentTranscriptV1 {
            assert!(value.construction.selected_transcript_units > 0);
            for record in &value.compilation.package.records {
                if let Payload::TranscriptUnit(unit) = &record.payload {
                    if observer == "mira" {
                        assert!(unit.original_input.is_none() && unit.narration.is_none());
                    }
                    if engine.scope().branch == "literal-golden" {
                        assert_ne!(unit.turn, "unicode-dialogue");
                        assert_ne!(unit.turn, "private-only");
                    }
                }
            }
        }
    }
    assert_eq!(observed.len(), 6);
    let expected: Vec<_> = EXPECTED
        .into_iter()
        .map(|(name, hash)| (name, hash.to_owned()))
        .collect();
    assert_eq!(observed, expected, "existing compiler bytes changed");
}
