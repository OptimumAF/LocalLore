//! Identical fixed probe runs on accepted old compiler and new compiler. Compare
//! emitted hashes, not timings; no copied compiler or fabricated expected bytes.
use locallore::{context_compiler::*, contracts::*, engine::Engine};
use sha2::{Digest, Sha256};

fn commit(e: &mut Engine, key: &str, commands: Vec<Command>) {
    let r = e.request(key, Intent::Actions(commands));
    let p = Engine::proposal(&r).unwrap();
    let n = e.preview(&r, &p).unwrap().narration().to_owned();
    e.commit(&r, &p, &n).unwrap();
}

#[test]
fn fixed_legacy_context_packages_have_reproducible_serialized_bytes() {
    let seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    let mut e = Engine::new(seed).unwrap();
    commit(
        &mut e,
        "opening",
        vec![
            Command::Promise {
                id: "beacon".into(),
                to: "mira".into(),
                terms: "Repair the old beacon".into(),
                deadline: 5000,
                return_item: None,
            },
            Command::Give {
                item: "potion".into(),
                to: "mira".into(),
                quantity: 1,
            },
        ],
    );
    for n in 0..24 {
        commit(
            &mut e,
            &format!("speech-{n}"),
            vec![Command::Say {
                text: format!("The old beacon ledger number {n} records shells."),
                audience: ["mira".into()].into(),
            }],
        );
    }
    let unchanged = (e.canonical_bytes(), e.receipts().to_vec());
    for (label, observer, role, at, query, reference, recent, optional) in [
        (
            "director",
            "player",
            Role::Director,
            None,
            "potion",
            None,
            4,
            16,
        ),
        (
            "character",
            "mira",
            Role::Character,
            None,
            "old beacon",
            None,
            4,
            16,
        ),
        (
            "historical",
            "mira",
            Role::Character,
            Some(2),
            "potion",
            None,
            4,
            16,
        ),
        (
            "referenced",
            "mira",
            Role::Character,
            None,
            "Mira",
            Some("mira"),
            4,
            16,
        ),
        (
            "mandatory-only",
            "mira",
            Role::Character,
            None,
            "",
            None,
            0,
            0,
        ),
    ] {
        let r = CompileRequest {
            version: COMPILER_VERSION,
            scope: e.scope().clone(),
            expected_head: e.revision(),
            at_revision: at,
            observer: observer.into(),
            role,
            query: query.into(),
            referenced_ids: reference.into_iter().map(str::to_owned).collect(),
            budget: Budget {
                recent_events: recent,
                optional_records: optional,
                ..Budget::default()
            },
        };
        let first = serde_json::to_vec(&compile(&e, &r).unwrap()).unwrap();
        let repeat = serde_json::to_vec(&compile_cancelled(&e, &r, &|| false).unwrap()).unwrap();
        assert_eq!(first, repeat);
        println!("LEGACY_CONTEXT_BYTES {label} {:x}", Sha256::digest(first));
    }
    assert_eq!(unchanged, (e.canonical_bytes(), e.receipts().to_vec()));
}
