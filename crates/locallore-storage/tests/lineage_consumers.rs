use locallore::{
    context_compiler::{compile, Budget, CompileRequest, Role, COMPILER_VERSION},
    contracts::*,
    engine::Engine,
    inspection_query::{query, Observer, Query, View, MAX_ROWS, QUERY_VERSION},
};
use locallore_storage::{
    derived_memory::{PrepareRequest, Target},
    ForkRequest, Store,
};

#[test]
fn durable_child_restart_feeds_shared_compiler_query_and_derived_preparation() {
    let path = std::env::temp_dir().join(format!(
        "locallore-lineage-{}-{}.sqlite",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos()
    ));
    let seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    let root = seed.scope.clone();
    let child;
    {
        let mut store = Store::open(&path, None).unwrap();
        store
            .create_story("Synthetic lineage consumers", seed)
            .unwrap();
        let apply = |store: &mut Store, scope: &Scope, key: &str, text: &str| {
            let e = store.resume(scope).unwrap().engine;
            let r = e.request(
                key,
                Intent::Actions(vec![Command::Say {
                    text: text.into(),
                    audience: ["mira".into()].into(),
                }]),
            );
            let p = Engine::proposal(&r).unwrap();
            let n = e.preview(&r, &p).unwrap().narration().to_owned();
            store.begin_turn(&r).unwrap();
            store.commit_turn(&r, &p, &n).unwrap();
        };
        apply(&mut store, &root, "inherited", "INHERITED-DURABLE");
        child = store
            .fork_branch(
                &ForkRequest {
                    parent: root.clone(),
                    child_branch: "child".into(),
                    expected_parent_revision: 1,
                    at_revision: 1,
                },
                &|| false,
            )
            .unwrap()
            .scope;
        apply(&mut store, &root, "future", "PARENT-FUTURE-DURABLE");
        apply(&mut store, &child, "local", "CHILD-DURABLE");
    }
    {
        let mut store = Store::open(&path, None).unwrap();
        let e = store.resume(&child).unwrap().engine;
        let before = e.canonical_bytes();
        let mut request = CompileRequest {
            version: COMPILER_VERSION,
            scope: child.clone(),
            expected_head: 2,
            at_revision: None,
            observer: "mira".into(),
            role: Role::Character,
            query: "DURABLE".into(),
            referenced_ids: vec![],
            budget: Budget::default(),
        };
        let now = serde_json::to_string(&compile(&e, &request).unwrap()).unwrap();
        assert!(now.contains("INHERITED-DURABLE") && now.contains("CHILD-DURABLE"));
        assert!(!now.contains("PARENT-FUTURE-DURABLE"));
        request.at_revision = Some(1);
        let old = serde_json::to_string(&compile(&e, &request).unwrap()).unwrap();
        assert!(old.contains("INHERITED-DURABLE") && !old.contains("CHILD-DURABLE"));
        let q = Query {
            version: QUERY_VERSION,
            scope: child.clone(),
            expected_head: 2,
            at_revision: None,
            observer: Observer::Character { id: "mira".into() },
            view: View::History,
            limit: MAX_ROWS,
            cursor: None,
            search: String::new(),
        };
        let page = query(&e, &q, true).unwrap();
        assert_eq!(page.total, 2);
        let rows = serde_json::to_string(&page.rows).unwrap();
        assert!(rows.contains("INHERITED-DURABLE") && rows.contains("CHILD-DURABLE"));
        assert!(!rows.contains("PARENT-FUTURE-DURABLE"));
        assert!(store
            .prepare_memory(
                &PrepareRequest {
                    scope: child.clone(),
                    expected_revision: 2,
                    observer: "mira".into(),
                    from_exclusive: 0,
                    through_revision: 2,
                    target: Target::SceneWindow
                },
                &|| false
            )
            .is_ok());
        assert_eq!(
            store.resume(&child).unwrap().engine.canonical_bytes(),
            before
        );
    }
    std::fs::remove_file(path).unwrap();
}
