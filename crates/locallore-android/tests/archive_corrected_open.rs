// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Real corrected archive -> fresh WorkspaceRegistry/Host reads. No JNI, device or model claim.
use locallore::{
    author_correction::{AuthorCorrectionInputV1, AuthorCorrectionOperationV1},
    contracts::*,
    engine::Engine,
};
use locallore_android::{archive::ArchiveRegistry, workspace::WorkspaceRegistry};
use locallore_storage::{ForkRequest, Store};
use serde_json::{json, Value};
use std::{
    path::{Path, PathBuf},
    sync::atomic::{AtomicU64, Ordering},
};

static NEXT: AtomicU64 = AtomicU64::new(0);
const OBSERVED: &str = "OBSERVED_OLD_PROPOSITION_70";
const TRUTH: &str = "PRIVATE_REPLACEMENT_TRUTH_70";
const REASON: &str = "PRIVATE_CORRECTION_REASON_70";
const BELIEF: &str = "PLAYER_BELIEF_ONLY_70";
const CLAIM: &str = "PLAYER_CLAIM_ONLY_70";
const FUTURE: &str = "PARENT_FUTURE_ONLY_70";
const NPC_BELIEF: &str = "MIRA_PRIVATE_BELIEF_70";

struct Fixture {
    directory: PathBuf,
    source: PathBuf,
    target: PathBuf,
    root: Scope,
    corrected: Scope,
    retired: Scope,
    control: Scope,
}
impl Fixture {
    fn new() -> Self {
        let directory = std::env::temp_dir().join(format!(
            "locallore-archive-corrected-open-{}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            NEXT.fetch_add(1, Ordering::Relaxed),
        ));
        #[cfg(windows)]
        assert!(directory.to_string_lossy().starts_with("D:"));
        std::fs::create_dir(&directory).unwrap();
        std::fs::write(
            directory.join("owner-v1"),
            b"synthetic-archive-corrected-open-v1",
        )
        .unwrap();
        let source = directory.join("source.sqlite3");
        let target = directory.join("target.sqlite3");
        let mut seed: Seed =
            serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
        seed.scope.story = "corrected-archive-70".into();
        let root = seed.scope.clone();
        let fact = seed.facts.get_mut("relic-location").unwrap();
        fact.proposition = OBSERVED.into();
        fact.discoverable_at = Some("quay".into());
        fact.known_by.clear(); // The first accepted action must actually discover event1.
        seed.beliefs[0].proposition = NPC_BELIEF.into();
        let mut belief = seed.beliefs[0].clone();
        belief.believer = seed.player.clone();
        belief.proposition = BELIEF.into();
        seed.beliefs.push(belief);
        let mut store = Store::open(&source, None).unwrap();
        store
            .create_story("Synthetic corrected archive", seed.clone())
            .unwrap();
        play(
            &mut store,
            &root,
            "before-correction",
            vec![
                Command::Discover {
                    fact: "relic-location".into(),
                },
                Command::Say {
                    text: CLAIM.into(),
                    audience: ["mira".into()].into(),
                },
            ],
        );
        assert_eq!(store.resume(&root).unwrap().engine.revision(), 2);
        let input = AuthorCorrectionInputV1 {
            version: 1,
            parent: root.clone(),
            expected_parent_revision: 2,
            fork_revision: 2,
            child_branch: "retired-correction".into(),
            operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
                fact: "relic-location".into(),
                expected_proposition: OBSERVED.into(),
                replacement: TRUTH.into(),
            },
            reason: REASON.into(),
        };
        let prepared = store.prepare_author_correction(&input, &|| false).unwrap();
        let outcome = store.apply_author_correction(&prepared, &|| false).unwrap();
        assert!(outcome.created);
        let retired = outcome.scope;
        let corrected = store
            .fork_branch(
                &ForkRequest {
                    parent: retired.clone(),
                    child_branch: "playable-corrected".into(),
                    expected_parent_revision: 3,
                    at_revision: 3,
                },
                &|| false,
            )
            .unwrap()
            .scope;
        let plan = store
            .prepare_branch_deletion(&retired, 3, &|| false)
            .unwrap();
        assert_eq!(
            store
                .delete_branch(plan, &|| false)
                .unwrap()
                .retained_through_revision,
            Some(3)
        );
        play(
            &mut store,
            &root,
            "parent-future",
            vec![Command::Say {
                text: FUTURE.into(),
                audience: ["mira".into()].into(),
            }],
        );
        assert_eq!(store.resume(&root).unwrap().engine.domain_version(), 1);
        let child = store.resume(&corrected).unwrap().engine;
        assert_eq!(child.domain_version(), 2); // Produced by an accepted correction, never a fixture flag.
        assert_eq!(
            child.effective_fact("relic-location").unwrap().proposition,
            TRUTH
        );
        assert_eq!(
            child.observed_facts("player", &corrected, 3).unwrap()["relic-location"].proposition,
            OBSERVED
        );
        drop(store);
        seed.scope.story = "control-archive-70".into();
        let control = seed.scope.clone();
        Store::open(&target, None)
            .unwrap()
            .create_story("Existing control", seed)
            .unwrap();
        Self {
            directory,
            source,
            target,
            root,
            corrected,
            retired,
            control,
        }
    }
    fn stage(&self, name: &str) -> PathBuf {
        let path = self.directory.join(name);
        std::fs::create_dir(&path).unwrap();
        path
    }
    fn export(&self, archives: &ArchiveRegistry) -> Vec<u8> {
        let owner = archives
            .open(&self.source, &self.stage("export-stage"))
            .unwrap();
        let request = serde_json::to_vec(&json!({"story":self.corrected.story,
            "branch":self.corrected.branch,"expected_revision":3}))
        .unwrap();
        let captured = data(decode(archives.prepare_export(owner, &request)));
        assert_eq!(captured["preview"]["version"], 3);
        assert_eq!(captured["preview"]["root_branch"], self.root.branch);
        assert!(captured["preview"]["retired_branch_ids"]
            .as_array()
            .unwrap()
            .contains(&json!(self.retired.branch)));
        let bytes = archives
            .export_bytes(owner, captured["token"].as_u64().unwrap())
            .unwrap();
        let text = std::str::from_utf8(&bytes).unwrap();
        assert!(text.contains(TRUTH) && text.contains(REASON) && text.contains(NPC_BELIEF));
        std::fs::write(
            self.directory.join("full-private-synthetic-v3.json"),
            &bytes,
        )
        .unwrap();
        archives.close(owner);
        bytes
    }
}
// Keep exclusively created synthetic databases, archives, stage records and marker on failure/success.
// There is deliberately no Drop cleanup; Root preserves closed-owner fixture evidence.

fn play(store: &mut Store, scope: &Scope, turn: &str, actions: Vec<Command>) {
    let engine = store.resume(scope).unwrap().engine;
    let request = engine.request(turn, Intent::Actions(actions));
    let prepared = engine
        .preview(&request, &Engine::proposal(&request).unwrap())
        .unwrap();
    store.begin_turn(&request).unwrap();
    store.commit_prepared(&prepared).unwrap();
}
fn canonical(path: &Path, scope: &Scope) -> (Vec<u8>, Vec<u8>) {
    let engine = Store::open(path, None)
        .unwrap()
        .resume(scope)
        .unwrap()
        .engine;
    (
        engine.canonical_bytes(),
        serde_json::to_vec(engine.canonical_records()).unwrap(),
    )
}
fn decode(bytes: Vec<u8>) -> Value {
    assert!(bytes.len() <= 262_144);
    serde_json::from_slice(&bytes).unwrap()
}
fn data(reply: Value) -> Value {
    assert_eq!(reply["version"], 1);
    assert_eq!(reply["status"], "ok", "{reply}");
    reply["data"].clone()
}
fn rejected(reply: Value, error: &str) {
    assert_eq!(
        reply,
        json!({"version":1,"status":"rejected","error":error})
    );
}
fn call(workspace: &WorkspaceRegistry, handle: u64, command: Value) -> Value {
    decode(workspace.call(
        handle,
        &serde_json::to_vec(&json!({"version":1,"command":command})).unwrap(),
    ))
}
fn resume(workspace: &WorkspaceRegistry, handle: u64, scope: &Scope) -> Value {
    data(call(
        workspace,
        handle,
        json!({"op":"resume","scope":scope}),
    ))
}
fn presentation(session: &Value) -> Value {
    json!({"op":"play_presentation_v2","session":session["session"],"scope":session["scope"],"expected_revision":3})
}
fn inspect(session: &Value, view: &str) -> Value {
    json!({"op":"inspection_query","session":session["session"],"query":{
        "version":2,"scope":session["scope"],"expected_head":3,"at_revision":null,
        "observer":{"kind":"player"},"view":view,"cursor":null,"limit":64,"search":""}})
}
fn no_private(value: &Value) {
    let text = value.to_string();
    for hidden in [TRUTH, REASON, NPC_BELIEF, FUTURE] {
        assert!(
            !text.contains(hidden),
            "private or parent-future canary leaked: {hidden}"
        );
    }
}

#[test]
fn actual_archive3_import_opens_original_root_then_playable_corrected_history_without_private_truth(
) {
    let fixture = Fixture::new();
    let source_before = [
        canonical(&fixture.source, &fixture.root),
        canonical(&fixture.source, &fixture.corrected),
    ];
    let control_before = canonical(&fixture.target, &fixture.control);
    let archives = ArchiveRegistry::default();
    let bytes = fixture.export(&archives);
    let owner = archives
        .open(&fixture.target, &fixture.stage("import-stage"))
        .unwrap();
    let prepared = data(decode(archives.prepare_import(owner, &bytes)));
    assert_eq!(
        Store::open(&fixture.target, None)
            .unwrap()
            .stories()
            .unwrap()
            .len(),
        1
    );
    let imported = data(decode(
        archives.commit_import(owner, prepared["token"].as_u64().unwrap()),
    ));
    assert_eq!(imported["root"], json!(fixture.root));
    assert_ne!(imported["root"], json!(fixture.corrected));
    archives.close(owner);
    assert_eq!(canonical(&fixture.target, &fixture.root), source_before[0]);
    assert_eq!(
        canonical(&fixture.target, &fixture.corrected),
        source_before[1]
    );

    let workspace = WorkspaceRegistry::default();
    let handle = workspace.open(&fixture.target).unwrap();
    let root_session = resume(&workspace, handle, &fixture.root);
    let root_view = data(call(&workspace, handle, presentation(&root_session)));
    assert_eq!(root_view["domain_version"], 1);
    assert_eq!(root_view["scope"], imported["root"]);
    assert_eq!(root_view["turns"].as_array().unwrap().len(), 2);
    assert!(root_view.to_string().contains(FUTURE));
    let catalog = data(call(
        &workspace,
        handle,
        json!({"op":"branches","story":fixture.root.story}),
    ));
    let branches = catalog["branches"].as_array().unwrap();
    assert!(branches
        .iter()
        .any(|branch| branch["scope"] == json!(fixture.corrected) && branch["retired"] == false));
    assert!(branches
        .iter()
        .any(|branch| branch["scope"] == json!(fixture.retired) && branch["retired"] == true));
    rejected(
        call(
            &workspace,
            handle,
            json!({"op":"resume","scope":fixture.retired}),
        ),
        "NotFound",
    );
    let session = resume(&workspace, handle, &fixture.corrected);
    rejected(
        call(
            &workspace,
            handle,
            json!({"op":"play_snapshot","session":session["session"],
        "scope":fixture.corrected,"expected_revision":3}),
        ),
        "Version",
    );
    let view = data(call(&workspace, handle, presentation(&session)));
    assert_eq!(view["version"], 2);
    assert_eq!(view["domain_version"], 2);
    assert_eq!(view["scope"], json!(fixture.corrected));
    assert_eq!(view["player"]["observer"], "player");
    assert_eq!(view["window"], json!({"total":1,"start":0,"end":1}));
    assert_eq!(view["turns"][0]["original_scope"], json!(fixture.root));
    assert_eq!(view["turns"][0]["event_ids"], json!([1, 2]));
    no_private(&view);

    let knowledge = data(call(&workspace, handle, inspect(&session, "knowledge")));
    let rows = knowledge["rows"].as_array().unwrap();
    assert!(knowledge["next_cursor"].is_null());
    let observed = rows
        .iter()
        .find(|row| row["origin"] == "known_as_observed" && row["id"] == "relic-location")
        .unwrap();
    assert_eq!(observed["text"], OBSERVED);
    assert_eq!(
        observed["sources"],
        json!([{"kind":"scoped_event","value":{"original_scope":fixture.root,"sequence":1}}])
    );
    for (origin, text) in [("subjective_belief", BELIEF), ("recorded_statement", CLAIM)] {
        assert!(rows
            .iter()
            .any(|row| row["origin"] == origin && row["text"] == text));
    }
    assert!(rows.iter().all(|row| row["origin"] != "canonical_truth"));
    no_private(&knowledge);
    let history = data(call(&workspace, handle, inspect(&session, "history")));
    assert!(history["rows"]
        .as_array()
        .unwrap()
        .contains(&json!({"kind":"author_correction","revision":3})));
    no_private(&history);
    let mut forbidden = inspect(&session, "knowledge");
    forbidden["query"]["observer"] = json!({"kind":"omniscient"});
    rejected(call(&workspace, handle, forbidden), "Forbidden");
    workspace.close(handle);

    let reopened = workspace.open(&fixture.target).unwrap();
    let fresh = resume(&workspace, reopened, &fixture.corrected);
    assert_eq!(data(call(&workspace, reopened, presentation(&fresh))), view);
    assert_eq!(
        data(call(&workspace, reopened, inspect(&fresh, "knowledge"))),
        knowledge
    );
    assert_eq!(
        data(call(&workspace, reopened, inspect(&fresh, "history"))),
        history
    );
    workspace.close(reopened);
    assert_eq!(canonical(&fixture.target, &fixture.root), source_before[0]);
    assert_eq!(
        canonical(&fixture.target, &fixture.corrected),
        source_before[1]
    );
    assert_eq!(canonical(&fixture.target, &fixture.control), control_before);
    assert_eq!(canonical(&fixture.source, &fixture.root), source_before[0]);
    assert_eq!(
        canonical(&fixture.source, &fixture.corrected),
        source_before[1]
    );
}

#[test]
fn cancelled_and_closed_import_capabilities_cannot_open_a_story_or_retarget_fresh_reads() {
    let fixture = Fixture::new();
    let control_before = canonical(&fixture.target, &fixture.control);
    let archives = ArchiveRegistry::default();
    let bytes = fixture.export(&archives);
    let stage = fixture.stage("cancel-import-stage");
    let owner = archives.open(&fixture.target, &stage).unwrap();
    let prepared = data(decode(archives.prepare_import(owner, &bytes)));
    let stale = prepared["token"].as_u64().unwrap();
    archives.cancel(owner);
    rejected(decode(archives.commit_import(owner, stale)), "InvalidToken");
    assert_eq!(
        Store::open(&fixture.target, None)
            .unwrap()
            .stories()
            .unwrap()
            .len(),
        1
    );
    assert_eq!(canonical(&fixture.target, &fixture.control), control_before);
    let fresh = data(decode(archives.prepare_import(owner, &bytes)))["token"]
        .as_u64()
        .unwrap();
    assert_ne!(fresh, stale);
    archives.close(owner);
    rejected(
        decode(archives.commit_import(owner, fresh)),
        "InvalidHandle",
    );
    assert_eq!(
        Store::open(&fixture.target, None)
            .unwrap()
            .stories()
            .unwrap()
            .len(),
        1
    );
    let new_owner = archives.open(&fixture.target, &stage).unwrap();
    rejected(
        decode(archives.commit_import(new_owner, fresh)),
        "InvalidToken",
    );
    let token = data(decode(archives.prepare_import(new_owner, &bytes)))["token"]
        .as_u64()
        .unwrap();
    let imported = data(decode(archives.commit_import(new_owner, token)));
    assert_eq!(imported["root"], json!(fixture.root));
    rejected(
        decode(archives.commit_import(new_owner, token)),
        "InvalidToken",
    );
    archives.close(new_owner);
    let corrected_before = canonical(&fixture.target, &fixture.corrected);
    let workspace = WorkspaceRegistry::default();
    let handle = workspace.open(&fixture.target).unwrap();
    let session = resume(&workspace, handle, &fixture.corrected);
    let command = presentation(&session);
    let mut stale_head = command.clone();
    stale_head["expected_revision"] = json!(2);
    rejected(call(&workspace, handle, stale_head), "Stale");
    let mut foreign_scope = command.clone();
    foreign_scope["scope"] = json!(fixture.root);
    rejected(call(&workspace, handle, foreign_scope), "Scope");
    no_private(&data(call(&workspace, handle, command.clone())));
    workspace.close(handle);
    let reopened = workspace.open(&fixture.target).unwrap();
    assert_ne!(reopened, handle);
    rejected(call(&workspace, handle, command.clone()), "InvalidHandle");
    rejected(call(&workspace, reopened, command), "Closed");
    let current = resume(&workspace, reopened, &fixture.corrected);
    assert_eq!(
        data(call(&workspace, reopened, presentation(&current)))["domain_version"],
        2
    );
    workspace.close(reopened);
    assert_eq!(
        canonical(&fixture.target, &fixture.corrected),
        corrected_before
    );
    assert_eq!(canonical(&fixture.target, &fixture.control), control_before);
}
