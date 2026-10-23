// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Independent public Host byte-route tests. No JNI, emulator or model claim.
use locallore::{contracts::*, engine::Engine, host::Host};
use locallore_android::workspace::WorkspaceRegistry;
use locallore_storage::{ForkRequest, Store};
use serde_json::{json, Value};
use std::{
    path::PathBuf,
    sync::atomic::{AtomicU64, Ordering},
};

static NEXT: AtomicU64 = AtomicU64::new(0);
struct Fixture {
    path: PathBuf,
    root: Scope,
    child: Scope,
    sibling: Scope,
    nested: Scope,
    other: Scope,
}
impl Fixture {
    fn new() -> Self {
        let directory = std::env::temp_dir().join(format!(
            "locallore-native-timeline-{}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&directory).unwrap();
        std::fs::write(
            directory.join("owner-v1"),
            b"locallore-native-timeline-synthetic-v1",
        )
        .unwrap();
        let path = directory.join("synthetic.sqlite");
        let mut store = Store::open(&path, None).unwrap();
        let mut seed: Seed =
            serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
        seed.scope.story = "native-timelines".into();
        let root = seed.scope.clone();
        store
            .create_story("Synthetic native timeline catalog", seed.clone())
            .unwrap();
        apply(&mut store, &root, "prefix", Command::Wait { ticks: 1 });
        let child = fork(&mut store, &root, "z-child", 1);
        apply(
            &mut store,
            &root,
            "same-key",
            Command::Give {
                item: "potion".into(),
                to: "mira".into(),
                quantity: 1,
            },
        );
        apply(
            &mut store,
            &child,
            "same-key",
            Command::Consume {
                item: "potion".into(),
            },
        );
        let sibling = fork(&mut store, &root, "a-sibling", 1);
        apply(
            &mut store,
            &sibling,
            "private-claim",
            Command::Say {
                text: "Synthetic sibling-private canary".into(),
                audience: ["mira".into()].into(),
            },
        );
        let nested = fork(&mut store, &child, "m-nested", 0);
        apply(
            &mut store,
            &nested,
            "rewound-wait",
            Command::Wait { ticks: 1 },
        );
        draft(&mut store, &root, "root-draft");
        draft(&mut store, &child, "child-draft-1");
        draft(&mut store, &child, "child-draft-2");
        seed.scope.story = "other-native-story".into();
        let other = seed.scope.clone();
        store
            .create_story("Independent native story", seed)
            .unwrap();
        apply(
            &mut store,
            &other,
            "other-private-claim",
            Command::Say {
                text: "Synthetic other-story canary".into(),
                audience: ["mira".into()].into(),
            },
        );
        Self {
            path,
            root,
            child,
            sibling,
            nested,
            other,
        }
    }
    fn store(&self) -> Store {
        Store::open(&self.path, None).unwrap()
    }
    fn catalog(&self, story: &str) -> Value {
        serde_json::to_value(self.store().branch_catalog(story, &|| false).unwrap()).unwrap()
    }
    fn state(&self, scope: &Scope) -> Vec<Vec<u8>> {
        let engine = self.store().resume(scope).unwrap().engine;
        let mut state = vec![
            engine.canonical_bytes(),
            serde_json::to_vec(engine.receipts()).unwrap(),
        ];
        for observer in ["player", "mira", "sable"] {
            state.push(
                serde_json::to_vec(
                    &engine
                        .character_context(observer, scope, engine.revision())
                        .unwrap(),
                )
                .unwrap(),
            );
        }
        state
    }
    fn archive(&self, scope: &Scope) -> Vec<u8> {
        self.store()
            .export_archive(&scope.story, &|| false)
            .unwrap()
            .bytes()
            .to_vec()
    }
}
// Retain only exclusively created synthetic roots under caller-owned TEMP.
// There is no recursive delete or arbitrary cleanup path in this test helper.
fn apply(store: &mut Store, scope: &Scope, id: &str, command: Command) {
    let engine = store.resume(scope).unwrap().engine;
    let request = engine.request(id, Intent::Actions(vec![command]));
    let receipt = engine
        .preview(&request, &Engine::proposal(&request).unwrap())
        .unwrap();
    store.begin_turn(&request).unwrap();
    store.commit_prepared(&receipt).unwrap();
}
fn draft(store: &mut Store, scope: &Scope, id: &str) {
    let e = store.resume(scope).unwrap().engine;
    store
        .begin_turn(&e.request(id, Intent::Actions(vec![Command::Wait { ticks: 1 }])))
        .unwrap();
}
fn fork(store: &mut Store, parent: &Scope, id: &str, at: u64) -> Scope {
    let head = store.resume(parent).unwrap().engine.revision();
    store
        .fork_branch(
            &ForkRequest {
                parent: parent.clone(),
                child_branch: id.into(),
                at_revision: at,
                expected_parent_revision: head,
            },
            &|| false,
        )
        .unwrap()
        .scope
}
fn call(registry: &WorkspaceRegistry, handle: u64, command: Value) -> Value {
    let raw = registry.call(
        handle,
        &serde_json::to_vec(&json!({"version":1,"command":command})).unwrap(),
    );
    assert!(raw.len() <= 262_144);
    serde_json::from_slice(&raw).unwrap()
}
fn data(reply: Value) -> Value {
    assert_eq!(reply["version"], 1);
    assert_eq!(
        reply["status"], "ok",
        "fixed error category: {}",
        reply["error"]
    );
    reply["data"].clone()
}
fn rejected(reply: Value, category: &str) {
    assert_eq!(
        reply,
        json!({"version":1,"status":"rejected","error":category})
    );
}
fn same<T: PartialEq>(a: &T, b: &T) {
    assert!(a == b, "synthetic native timeline parity differed");
}
fn resume(registry: &WorkspaceRegistry, handle: u64, scope: &Scope) -> Value {
    data(call(registry, handle, json!({"op":"resume","scope":scope})))
}
fn close_session(registry: &WorkspaceRegistry, handle: u64, session: &Value) {
    data(call(
        registry,
        handle,
        json!({"op":"close","session":session["session"],"scope":session["scope"]}),
    ));
}
fn scoped(session: &Value, op: &str, key: &str) -> Value {
    json!({"op":op,"session":session["session"],"scope":session["scope"],"turn":key})
}
fn snapshot(registry: &WorkspaceRegistry, handle: u64, session: &Value, head: u64) -> Value {
    data(call(
        registry,
        handle,
        json!({"op":"play_snapshot","session":session["session"],"scope":session["scope"],"expected_revision":head}),
    ))
}
fn catalog(registry: &WorkspaceRegistry, handle: u64, story: &str) -> Value {
    let reply = call(registry, handle, json!({"op":"branches","story":story}));
    assert!(serde_json::to_vec(&reply).unwrap().len() <= 64 * 1024);
    data(reply)
}

#[test]
fn public_catalog_has_exact_typed_metadata_and_keeps_workspace_library_root_only_without_writes() {
    let f = Fixture::new();
    let expected = f.catalog(&f.root.story);
    let other = f.catalog(&f.other.story);
    let baseline = std::fs::read(&f.path).unwrap();
    let archive = f.archive(&f.root);
    let states: Vec<_> = [&f.root, &f.child, &f.sibling, &f.nested, &f.other]
        .into_iter()
        .map(|s| f.state(s))
        .collect();
    let registry = WorkspaceRegistry::default();
    let h = registry.open(&f.path).unwrap();
    for _ in 0..3 {
        same(&expected, &catalog(&registry, h, &f.root.story));
    }
    same(&other, &catalog(&registry, h, &f.other.story));
    let branches = expected["branches"].as_array().unwrap();
    assert_eq!(branches.len(), 4);
    assert_eq!(
        branches
            .iter()
            .map(|b| b["scope"]["branch"].as_str().unwrap())
            .collect::<Vec<_>>(),
        ["a-sibling", "m-nested", "main", "z-child"]
    );
    assert_eq!(
        (
            branches[2]["revision"].as_u64(),
            branches[2]["drafts"].as_u64()
        ),
        (Some(2), Some(1))
    );
    assert_eq!(
        (
            branches[3]["parent_branch"].as_str(),
            branches[3]["fork_revision"].as_u64(),
            branches[3]["revision"].as_u64(),
            branches[3]["drafts"].as_u64()
        ),
        (Some("main"), Some(1), Some(2), Some(2))
    );
    assert_eq!(
        (
            branches[1]["parent_branch"].as_str(),
            branches[1]["fork_revision"].as_u64(),
            branches[1]["revision"].as_u64()
        ),
        (Some("z-child"), Some(0), Some(1))
    );
    let library = data(call(&registry, h, json!({"op":"workspace"})));
    let stories = library["stories"].as_array().unwrap();
    assert_eq!(stories.len(), 2);
    assert!(stories.iter().all(|s| s["scope"]["branch"] == "main"));
    let encoded = serde_json::to_string(&expected).unwrap();
    for private in [
        "canary",
        "SECRET-TIDE",
        "local_receipts",
        "seed",
        "narration",
    ] {
        assert!(!encoded.contains(private));
    }
    registry.close(h);
    same(&baseline, &std::fs::read(&f.path).unwrap());
    same(&archive, &f.archive(&f.root));
    for (scope, state) in [&f.root, &f.child, &f.sibling, &f.nested, &f.other]
        .into_iter()
        .zip(states)
    {
        same(&state, &f.state(scope));
    }
}

#[test]
fn actual_child_resume_continues_original_scoped_history_and_retries_after_owner_reopen() {
    let f = Fixture::new();
    let unaffected: Vec<_> = [&f.root, &f.sibling, &f.nested, &f.other]
        .into_iter()
        .map(|s| f.state(s))
        .collect();
    let other_archive = f.archive(&f.other);
    let registry = WorkspaceRegistry::default();
    let h = registry.open(&f.path).unwrap();
    for scope in [&f.root, &f.child, &f.sibling, &f.nested] {
        let e = f.store().resume(scope).unwrap().engine;
        let s = resume(&registry, h, scope);
        assert_eq!(s["revision"], e.revision());
        let view = snapshot(&registry, h, &s, e.revision());
        same(
            &view["receipts"],
            &serde_json::to_value(e.receipts()).unwrap(),
        );
        let context = data(call(
            &registry,
            h,
            json!({"op":"inspect","session":s["session"],"scope":scope,"observer":"player","expected_revision":e.revision()}),
        ));
        same(
            &context["context"],
            &serde_json::to_value(e.character_context("player", scope, e.revision()).unwrap())
                .unwrap(),
        );
        if scope != &f.sibling {
            assert!(!serde_json::to_string(&view)
                .unwrap()
                .contains("sibling-private canary"));
        }
        assert!(!serde_json::to_string(&view)
            .unwrap()
            .contains("other-story canary"));
        close_session(&registry, h, &s);
    }
    let child = resume(&registry, h, &f.child);
    let old = f
        .store()
        .lookup_turn(&f.child, "same-key")
        .unwrap()
        .receipt
        .unwrap();
    same(
        &data(call(&registry, h, scoped(&child, "commit", "same-key")))["receipt"],
        &serde_json::to_value(&old).unwrap(),
    );
    let request = json!({"version":1,"scope":f.child,"turn":"native-child-wait","expected_revision":2,"intent":{"kind":"actions","value":[{"op":"wait","ticks":1}]}});
    assert_eq!(
        data(call(
            &registry,
            h,
            json!({"op":"submit","session":child["session"],"request":request,"mode":"accepted"})
        ))["phase"],
        "queued"
    );
    assert_eq!(
        data(call(
            &registry,
            h,
            scoped(&child, "prepare", "native-child-wait")
        ))["phase"],
        "ready"
    );
    let committed = data(call(
        &registry,
        h,
        scoped(&child, "commit", "native-child-wait"),
    ));
    assert_eq!(committed["phase"], "committed");
    same(&committed["receipt"]["request"], &request);
    assert_eq!(
        committed["receipt"]["events"][0]["scope"],
        serde_json::to_value(&f.child).unwrap()
    );
    same(
        &committed,
        &data(call(
            &registry,
            h,
            scoped(&child, "commit", "native-child-wait"),
        )),
    );
    assert_eq!(
        snapshot(&registry, h, &child, 3)["receipts"]
            .as_array()
            .unwrap()
            .len(),
        3
    );
    let updated = catalog(&registry, h, &f.root.story);
    assert_eq!(updated["branches"][3]["revision"], 3);
    assert_eq!(updated["branches"][2]["revision"], 2);
    registry.close(h);
    let reopened = registry.open(&f.path).unwrap();
    let resumed = resume(&registry, reopened, &f.child);
    assert_eq!(resumed["revision"], 3);
    same(
        &committed,
        &data(call(
            &registry,
            reopened,
            scoped(&resumed, "commit", "native-child-wait"),
        )),
    );
    registry.close(reopened);
    for (scope, state) in [&f.root, &f.sibling, &f.nested, &f.other]
        .into_iter()
        .zip(unaffected)
    {
        same(&state, &f.state(scope));
    }
    same(&other_archive, &f.archive(&f.other));
    assert_eq!(
        f.store().resume(&f.child).unwrap().engine.receipts().len(),
        3
    );
}

#[test]
fn malformed_authority_and_cross_scope_inputs_reject_without_metadata_or_canonical_change() {
    let f = Fixture::new();
    let baseline = std::fs::read(&f.path).unwrap();
    let registry = WorkspaceRegistry::default();
    let h = registry.open(&f.path).unwrap();
    for command in [
        json!({"op":"branches","story":f.root.story,"observer":"omniscient"}),
        json!({"op":"branches","story":f.root.story,"story_lab":true}),
        json!({"op":"branches","story":f.root.story,"scope":f.child}),
        json!({"op":"branches","story":{ "story":f.root.story}}),
    ] {
        rejected(call(&registry, h, command), "Malformed");
    }
    for id in ["", "foreign/story", "private\ncanary", &"x".repeat(65)] {
        rejected(
            call(&registry, h, json!({"op":"branches","story":id})),
            "Scope",
        );
    }
    rejected(
        call(
            &registry,
            h,
            json!({"op":"branches","story":"unknown-story"}),
        ),
        "NotFound",
    );
    let mixed = Scope {
        story: f.other.story.clone(),
        branch: f.child.branch.clone(),
    };
    rejected(
        call(&registry, h, json!({"op":"resume","scope":mixed})),
        "NotFound",
    );
    let s = resume(&registry, h, &f.root);
    for observer in ["mira", "sable", "omniscient"] {
        rejected(
            call(
                &registry,
                h,
                json!({"op":"inspect","session":s["session"],"scope":f.root,"observer":observer,"expected_revision":2}),
            ),
            "Forbidden",
        );
    }
    rejected(
        call(
            &registry,
            h,
            json!({"op":"inspect","session":s["session"],"scope":f.child,"observer":"player","expected_revision":2}),
        ),
        "Scope",
    );
    rejected(
        serde_json::from_slice(&registry.call(h, &vec![b'x'; 24_577])).unwrap(),
        "TooLarge",
    );
    rejected(
        serde_json::from_slice(&registry.call(h, b"private malformed canary")).unwrap(),
        "Malformed",
    );
    let ephemeral = Host::new(false);
    rejected(
        ephemeral.call(
            &serde_json::to_vec(
                &json!({"version":1,"command":{"op":"branches","story":f.root.story}}),
            )
            .unwrap(),
        ),
        "Unsupported",
    );
    registry.close(h);
    same(&baseline, &std::fs::read(&f.path).unwrap());
}

#[test]
fn catalog_dispatch_releases_all_four_native_owners_and_closed_handles_never_rebind() {
    let f = Fixture::new();
    let baseline = std::fs::read(&f.path).unwrap();
    let expected = f.catalog(&f.root.story);
    let registry = WorkspaceRegistry::default();
    let handles: Vec<_> = (0..4).map(|_| registry.open(&f.path).unwrap()).collect();
    assert_eq!(registry.open(&f.path).err(), Some("WorkspaceLimit".into()));
    for h in &handles {
        same(&expected, &catalog(&registry, *h, &f.root.story));
        registry.close(*h);
        registry.close(*h);
        rejected(
            call(&registry, *h, json!({"op":"branches","story":f.root.story})),
            "InvalidHandle",
        );
    }
    let replacement: Vec<_> = (0..4).map(|_| registry.open(&f.path).unwrap()).collect();
    assert_eq!(registry.open(&f.path).err(), Some("WorkspaceLimit".into()));
    for h in replacement {
        assert!(!handles.contains(&h));
        same(&expected, &catalog(&registry, h, &f.root.story));
        registry.close(h);
    }
    same(&baseline, &std::fs::read(&f.path).unwrap());
}
