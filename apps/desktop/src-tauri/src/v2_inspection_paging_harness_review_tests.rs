// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Independent FIRST at c4f59058, with Root893e5824 negative-control precision.
//! SOURCE ONLY / UNREGISTERED / UNCOMPILED / UNRUN. Missing module/helpers or
//! admitted D05 environment is SETUP_UNRUN, never a zero-test pass/behavior RED.
//! Actual fixture execution also requires Windows create_new_pinned support;
//! there is no weaker non-Windows producer or temporary-directory fallback.
//! Actual fixed helper + production Workspace/Host/Store/Engine APIs. No copied
//! producer, fake Persistence, provider, SQL, private session or page construction.
//! Seven ordinary fixture databases/files maximum plus the one tiny-file control:
//! one template, five <=8MiB closed DB copies, one empty Store, one tiny file.
//! Retain every root on failure/success. No Drop cleanup or environment mutation.
//! The91 setup API calls are a SOURCE-REVIEWED roster, not invocation telemetry.
//! Tests can prove45 canonical records/44 committed ordinary turns. These are not
//! IPC/WebView/render/focus/model/SDK/OS-isolation or whole-D05 acceptance tests.
use super::*;
use locallore::{
    author_correction::{AuthorCorrectionInputV1, AuthorCorrectionOperationV1},
    contracts::{Command, Intent, Receipt, Request, Scope, Seed},
    engine::Engine,
    host::Host,
    inspection_query::{Observer, Page, Query, Row, View},
};
use locallore_storage::{Store, TurnPhase};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs::{self, OpenOptions},
    io::Write,
    path::{Path, PathBuf},
    sync::{Mutex, OnceLock},
};

const PRIMARY: &str = "d05-inspector-native";
const OTHER: &str = "d05-inspector-other";
const PLAYER_SECRET: &str = "D05_PLAYER_SEED_SECRET_731";
const MIRA_BELIEF: &str = "D05_MIRA_PRIVATE_BELIEF_812";
const AUTHOR_TRUTH: &str = "D05_UNOBSERVED_AUTHOR_TRUTH_913";
const AUTHOR_REASON: &str = "D05_AUTHOR_REASON_PRIVATE_914";
const OTHER_SECRET: &str = "D05_OTHER_STORY_SEED_515";
const OTHER_MESSAGE: &str = "D05_OTHER_STORY_MESSAGE_516";
const COPY_CAP: u64 = 8 * 1024 * 1024;
static TEMPLATE_IO: Mutex<()> = Mutex::new(());

fn scopes() -> [Scope; 3] {
    [
        Scope {
            story: PRIMARY.into(),
            branch: "main".into(),
        },
        Scope {
            story: PRIMARY.into(),
            branch: "paging".into(),
        },
        Scope {
            story: OTHER.into(),
            branch: "main".into(),
        },
    ]
}
fn packet() -> PathBuf {
    let admitted = std::env::var_os("LOCALLORE_D05_ARTIFACT_ROOT")
        .expect("SETUP_UNRUN: Root must admit an existing D05 artifact base");
    let admitted = PathBuf::from(admitted);
    assert!(
        admitted.is_absolute() && admitted.is_dir(),
        "SETUP_UNRUN: existing absolute D05 base"
    );
    let parent = fs::canonicalize(admitted).unwrap();
    #[cfg(windows)]
    {
        use std::path::{Component, Prefix};
        assert!(
            matches!(parent.components().next(), Some(Component::Prefix(p))
            if matches!(p.kind(), Prefix::Disk(d) | Prefix::VerbatimDisk(d) if d.eq_ignore_ascii_case(&b'D'))),
            "SETUP_UNRUN: physical D artifact admission"
        );
    }
    for ancestor in parent.ancestors() {
        let metadata = fs::symlink_metadata(ancestor).unwrap();
        assert!(metadata.is_dir() && !metadata.file_type().is_symlink());
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt;
            assert_eq!(metadata.file_attributes() & 0x400, 0);
        }
    }
    let root = parent.join(format!(
        "d05-v2-inspector-paging-native-{}",
        crate::exports::identifier().unwrap()
    ));
    fs::create_dir(&root).unwrap();
    root
}
fn database(root: &Path) -> PathBuf {
    root.join("stories-v1.sqlite")
}
fn template() -> &'static Path {
    static ORIGINAL: OnceLock<std::result::Result<PathBuf, ()>> = OnceLock::new();
    ORIGINAL
        .get_or_init(|| {
            std::panic::catch_unwind(|| {
                let path = database(&packet());
                prepare_fixture(&path).unwrap();
                assert!(
                    fs::metadata(&path).unwrap().len() <= COPY_CAP,
                    "retain oversized original; never replace it"
                );
                path
            })
            .map_err(|_| ())
        })
        .as_ref()
        .expect("original fixture failed; retained, no replacement setup attempt")
        .as_path()
}
fn copied_fixture() -> PathBuf {
    let source = template();
    let _closed = TEMPLATE_IO.lock().expect("retain failed template owner");
    // The only other template reader (recipe/oracle test) holds this same lock
    // until all its Store/Host handles are dropped. No live/writable DB is copied.
    let metadata = fs::symlink_metadata(source).unwrap();
    assert!(metadata.is_file() && !metadata.file_type().is_symlink() && metadata.len() <= COPY_CAP);
    let before = fs::read(source).unwrap();
    assert_eq!(before.len() as u64, metadata.len());
    let target = database(&packet());
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&target)
        .unwrap();
    file.write_all(&before).unwrap();
    file.sync_all().unwrap();
    drop(file);
    assert_eq!(fs::read(&target).unwrap(), before);
    assert_eq!(fs::read(source).unwrap(), before);
    target
}
fn sha(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}
fn encoded<T: serde::Serialize + ?Sized>(value: &T) -> Vec<u8> {
    serde_json::to_vec(value).unwrap()
}
fn keys(value: &Value) -> BTreeSet<&str> {
    value
        .as_object()
        .unwrap()
        .keys()
        .map(String::as_str)
        .collect()
}
fn correction() -> AuthorCorrectionInputV1 {
    AuthorCorrectionInputV1 {
        version: 1,
        parent: scopes()[0].clone(),
        expected_parent_revision: 0,
        fork_revision: 0,
        child_branch: "paging".into(),
        reason: AUTHOR_REASON.into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: "beacon-mark".into(),
            expected_proposition: "An old repair mark is scratched inside the dry well.".into(),
            replacement: AUTHOR_TRUTH.into(),
        },
    }
}
fn actual_scope_evidence(store: &mut Store, scope: &Scope, index: usize) -> Value {
    let engine = store.resume(scope).unwrap().engine;
    let actors = [engine.seed().player.as_str(), "mira", "oren", "sable"]
        .into_iter()
        .map(|id| {
            (
                id.to_owned(),
                engine
                    .character_context_v2(id, scope, engine.revision())
                    .unwrap(),
                engine
                    .actor_receipts_v2(id, scope, engine.revision())
                    .unwrap(),
            )
        })
        .collect::<Vec<_>>();
    let turns = if index == 1 {
        (1..=43)
            .map(|n| format!("d05-page-{n:03}"))
            .collect::<Vec<_>>()
    } else if index == 2 {
        vec!["d05-other-001".into()]
    } else {
        vec![]
    };
    let turns = turns
        .into_iter()
        .map(|key| {
            let turn = store.lookup_turn(scope, &key).unwrap();
            assert!(matches!(turn.phase, TurnPhase::Committed));
            let receipt = turn.receipt.unwrap();
            assert_eq!(receipt.request(), &turn.request);
            (key, "committed", turn.request, receipt)
        })
        .collect::<Vec<(String, &'static str, Request, Receipt)>>();
    json!({"scope":scope,"domain_version":engine.domain_version(),"head":engine.revision(),
        "story_time":engine.state().story_time,"seed_sha256":sha(&encoded(engine.seed())),
        "projection_sha256":sha(&engine.canonical_bytes()),
        "records_sha256":sha(&encoded(engine.canonical_records())),
        "receipts_sha256":sha(&encoded(engine.receipts())),
        "turns_sha256":sha(&encoded(&turns)),"actors_sha256":sha(&encoded(&actors))})
}
fn actual_evidence(path: &Path) -> Value {
    let mut store = Store::open_read_only(path).unwrap();
    let values = scopes()
        .iter()
        .enumerate()
        .map(|(index, scope)| actual_scope_evidence(&mut store, scope, index))
        .collect::<Vec<_>>();
    json!({"version":1,"kind":"v2_inspection_paging_oracle_v1","fixture_version":1,"scopes":values})
}
fn wire(host: &Host, command: Value) -> Value {
    let response: Value = host.call(&encoded(&json!({"version":1,"command":command})));
    assert_eq!(response["version"], 1);
    assert_eq!(response["status"], "ok", "actual Host response: {response}");
    response["data"].clone()
}
fn resume(host: &Host, scope: &Scope, head: u64) -> String {
    let result = wire(host, json!({"op":"resume","scope":scope}));
    assert_eq!(result["scope"], json!(scope));
    assert_eq!(result["revision"], head);
    result["session"].as_str().unwrap().to_owned()
}
fn query(
    scope: &Scope,
    head: u64,
    observer: Observer,
    view: View,
    at_revision: Option<u64>,
    search: &str,
) -> Query {
    Query {
        version: 2,
        scope: scope.clone(),
        expected_head: head,
        at_revision,
        observer,
        view,
        cursor: None,
        limit: 64,
        search: search.into(),
    }
}
fn pages(
    host: &Host,
    session: &str,
    original: &Query,
    total: usize,
    lengths: &[usize],
) -> Vec<Page> {
    let mut request = original.clone();
    let mut output = vec![];
    for expected in lengths {
        let page = host.inspection_query(session, &request).unwrap();
        assert_eq!(page.rows.len(), *expected);
        assert_eq!(page.total, total);
        assert_eq!(page.scope, original.scope);
        assert_eq!(page.head, original.expected_head);
        assert_eq!(
            page.revision,
            original.at_revision.unwrap_or(original.expected_head)
        );
        assert_eq!(page.story_time, 100);
        assert!(encoded(&page).len() <= 65_536);
        assert!(page.rows.iter().all(|row| encoded(row).len() <= 768));
        assert!(page
            .rows
            .windows(2)
            .all(|pair| pair[0].key() < pair[1].key()));
        if let Some(cursor) = &page.next_cursor {
            assert!(cursor.len() <= 128);
        }
        request.cursor = page.next_cursor.clone();
        output.push(page);
    }
    assert!(output.last().unwrap().next_cursor.is_none());
    let all = output
        .iter()
        .flat_map(|page| page.rows.iter().map(Row::key))
        .collect::<Vec<_>>();
    assert_eq!(all.len(), total);
    assert!(all.windows(2).all(|pair| pair[0] < pair[1]));
    output
}

#[test]
fn exact_mode_selection_is_pure_and_never_turns_requested_invalid_into_absent() {
    let before: BTreeMap<_, _> = std::env::vars_os().collect();
    for mask in 0..8 {
        let development = mask & 1 != 0;
        let legacy = mask & 2 != 0;
        let other = mask & 4 != 0;
        assert_eq!(validate_mode(None, development, legacy, other), Ok(false));
        assert_eq!(
            validate_mode(Some("1"), development, legacy, other),
            if mask == 1 {
                Ok(true)
            } else {
                Err("Forbidden".into())
            }
        );
        for invalid in ["", "0", "true", "01", " 1", "1 ", "restart", "\0"] {
            assert_eq!(
                validate_mode(Some(invalid), development, legacy, other),
                Err("Forbidden".into())
            );
        }
    }
    assert_eq!(std::env::vars_os().collect::<BTreeMap<_, _>>(), before);
}

#[test]
fn fixed_path_and_readonly_open_guards_preserve_absent_and_existing_ordinary_targets() {
    let root = packet();
    let path = database(&root);
    assert_eq!(validate_workspace_path(&path), Ok(()));
    assert_eq!(fixture_oracle(&path).unwrap_err(), "SyntheticReadOnly");
    assert!(!path.try_exists().unwrap());
    for bad in [root.join("other.sqlite"), root.join("nested/stories-v1.sqlite"),
        PathBuf::from(format!("{}/./stories-v1.sqlite", root.display())),
        PathBuf::from(format!("{}/nested/../stories-v1.sqlite", root.display())),
        root.join("d05-v2-inspector-paging-native-AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA/stories-v1.sqlite"),
        PathBuf::from("C:/ordinary/d05-v2-inspector-paging-native-00000000-0000-0000-0000-000000000001/stories-v1.sqlite")] {
        assert_eq!(validate_workspace_path(&bad), Err("SyntheticWorkspaceRequired".into()));
    }
    let original = b"retained non-SQLite negative control";
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&path)
        .unwrap();
    file.write_all(original).unwrap();
    file.sync_all().unwrap();
    drop(file);
    assert_eq!(validate_workspace_path(&path), Ok(()));
    assert_eq!(
        prepare_fixture(&path),
        Err("SyntheticFreshWorkspaceRequired".into())
    );
    assert_eq!(fixture_oracle(&path).unwrap_err(), "SyntheticReadOnly");
    assert_eq!(fs::read(&path).unwrap(), original);
}

#[test]
fn actual_recipe_has_exact_seed_fork_receipts_and_readonly_oracle_tuple_hashes() {
    let _closed = TEMPLATE_IO.lock().unwrap();
    let path = template();
    let mut store = Store::open_read_only(path).unwrap();
    let roots = store.stories().unwrap();
    assert_eq!(
        roots.len(),
        2,
        "workspace library lists root stories, not all three scopes"
    );
    assert_eq!(
        roots
            .iter()
            .map(|story| story.scope.clone())
            .collect::<Vec<_>>(),
        vec![scopes()[0].clone(), scopes()[2].clone()]
    );
    let mut expected_primary: Seed =
        serde_json::from_str(include_str!("../../../../fixtures/lantern_quay.json")).unwrap();
    expected_primary.scope = scopes()[0].clone();
    expected_primary
        .facts
        .get_mut("relic-location")
        .unwrap()
        .proposition = PLAYER_SECRET.into();
    expected_primary
        .beliefs
        .iter_mut()
        .find(|belief| belief.believer == "mira")
        .unwrap()
        .proposition = MIRA_BELIEF.into();
    let mut expected_other: Seed =
        serde_json::from_str(include_str!("../../../../fixtures/lantern_quay.json")).unwrap();
    expected_other.scope = scopes()[2].clone();
    expected_other
        .facts
        .get_mut("relic-location")
        .unwrap()
        .proposition = OTHER_SECRET.into();
    let mut records = 0;
    let mut receipts = 0;
    for (index, scope) in scopes().iter().enumerate() {
        let engine = store.resume(scope).unwrap().engine;
        assert_eq!(engine.domain_version(), [1, 2, 1][index]);
        assert_eq!(engine.revision(), [0, 44, 1][index]);
        assert_eq!(engine.state().story_time, 100);
        let seed = if index == 2 {
            &expected_other
        } else {
            &expected_primary
        };
        assert_eq!(encoded(engine.seed()), encoded(seed));
        assert_eq!(encoded(&engine.state().actors), encoded(&seed.actors));
        assert_eq!(encoded(&engine.state().items), encoded(&seed.items));
        assert_eq!(engine.receipts().len(), [0, 43, 1][index]);
        records += engine.canonical_record_count();
        receipts += engine.receipts().len();
        let turns = if index == 1 {
            (1..=43)
                .map(|i| (format!("d05-page-{i:03}"), i))
                .collect::<Vec<_>>()
        } else if index == 2 {
            vec![("d05-other-001".into(), 1)]
        } else {
            vec![]
        };
        for (key, i) in turns {
            let saved = store.lookup_turn(scope, &key).unwrap();
            assert!(matches!(saved.phase, TurnPhase::Committed));
            let receipt = saved.receipt.unwrap();
            assert_eq!(receipt.request(), &saved.request);
            assert_eq!(receipt.events().len(), 1);
            assert_eq!(
                receipt.events()[0].sequence(),
                if index == 1 { i + 1 } else { 1 }
            );
            assert_eq!(
                saved.request.expected_revision,
                if index == 1 { i } else { 0 }
            );
            let expected_text = if index == 2 {
                OTHER_MESSAGE.into()
            } else {
                format!(
                    "D05_PAGING_ROW_{i:03}{}",
                    if i % 2 == 1 { "_MIRA" } else { "_PLAYER_ONLY" }
                )
            };
            let expected_audience: BTreeSet<String> = [if index == 2 || i % 2 == 1 {
                "mira".into()
            } else {
                seed.player.clone()
            }]
            .into();
            match &saved.request.intent {
                Intent::Dialogue { text, audience } => {
                    assert_eq!(text, &expected_text);
                    assert_eq!(audience, &expected_audience);
                }
                _ => panic!("actual fixed ordinary turn must be Dialogue"),
            }
            assert_eq!(
                encoded(receipt.proposal()),
                encoded(&Engine::proposal(&saved.request).unwrap())
            );
            assert_eq!(
                receipt.narration(),
                "Your words are heard by the chosen listeners."
            );
        }
    }
    assert_eq!((records, receipts), (45, 44));
    drop(store);
    let actual = fixture_oracle(path).unwrap();
    assert_eq!(
        keys(&actual),
        ["version", "kind", "fixture_version", "scopes"].into()
    );
    assert_eq!(actual, actual_evidence(path));
    assert!(encoded(&actual).len() <= 32 * 1024);
    for item in actual["scopes"].as_array().unwrap() {
        assert_eq!(
            keys(item),
            [
                "scope",
                "domain_version",
                "head",
                "story_time",
                "seed_sha256",
                "projection_sha256",
                "records_sha256",
                "receipts_sha256",
                "turns_sha256",
                "actors_sha256"
            ]
            .into()
        );
        for name in [
            "seed_sha256",
            "projection_sha256",
            "records_sha256",
            "receipts_sha256",
            "turns_sha256",
            "actors_sha256",
        ] {
            let hash = item[name].as_str().unwrap();
            assert_eq!(hash.len(), 64);
            assert!(hash
                .bytes()
                .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b)));
        }
    }
    let before = fs::read(path).unwrap();
    assert_eq!(
        prepare_fixture(path),
        Err("SyntheticFreshWorkspaceRequired".into())
    );
    assert_eq!(fs::read(path).unwrap(), before);
    assert_eq!(fixture_oracle(path).unwrap(), actual);
}

#[test]
fn actual_host_current_historical_search_and_marker_pages_match_the_fixed_roster() {
    let path = copied_fixture();
    let before = fixture_oracle(&path).unwrap();
    let host = locallore_workspace::open(&path, true).unwrap();
    let child = scopes()[1].clone();
    let session = resume(&host, &child, 44);
    let branches = wire(&host, json!({"op":"branches","story":PRIMARY}));
    assert_eq!(branches["version"], 2);
    assert_eq!(branches["branches"].as_array().unwrap().len(), 2);
    let paging = branches["branches"]
        .as_array()
        .unwrap()
        .iter()
        .find(|branch| branch["scope"] == json!(child))
        .unwrap();
    assert_eq!(paging["parent_branch"], "main");
    assert_eq!(paging["fork_revision"], 0);
    assert_eq!(paging["revision"], 44);
    assert_eq!(paging["retired"], false);
    for (observer, at, total, lengths) in [
        (Observer::Player, None, 130, vec![64, 64, 2]),
        (Observer::Omniscient, None, 129, vec![64, 64, 1]),
        (
            Observer::Character { id: "mira".into() },
            None,
            22,
            vec![22],
        ),
        (Observer::Character { id: "sable".into() }, None, 0, vec![0]),
        (Observer::Player, Some(23), 67, vec![64, 3]),
        (Observer::Omniscient, Some(23), 66, vec![64, 2]),
        (
            Observer::Character { id: "mira".into() },
            Some(23),
            11,
            vec![11],
        ),
        (Observer::Player, Some(1), 1, vec![1]),
    ] {
        let q = query(&child, 44, observer.clone(), View::History, at, "");
        let got = pages(&host, &session, &q, total, &lengths);
        let raw = String::from_utf8(encoded(&got)).unwrap();
        for secret in [
            PLAYER_SECRET,
            MIRA_BELIEF,
            AUTHOR_TRUTH,
            AUTHOR_REASON,
            OTHER_SECRET,
            OTHER_MESSAGE,
        ] {
            assert!(!raw.contains(secret));
        }
        let rows = got.iter().flat_map(|page| &page.rows).collect::<Vec<_>>();
        if matches!(observer, Observer::Player) {
            assert_eq!(
                rows.iter()
                    .filter(|row| matches!(row, Row::AuthorCorrection { .. }))
                    .count(),
                1
            );
            let marker = rows
                .iter()
                .find(|row| matches!(row, Row::AuthorCorrection { .. }))
                .unwrap();
            assert_eq!(
                serde_json::to_value(marker).unwrap(),
                json!({"kind":"author_correction","revision":1}),
                "marker wire has no key"
            );
        } else {
            assert!(rows
                .iter()
                .all(|row| !matches!(row, Row::AuthorCorrection { .. })));
        }
        if let Observer::Character { id } = observer {
            assert!(rows.iter().all(|row| matches!(row, Row::Event { .. })));
            if id == "mira" {
                for row in rows {
                    if let Row::Event { event, .. } = row {
                        assert_eq!(event.sequence % 2, 0);
                    }
                }
            }
            assert!(!raw.contains("_PLAYER_ONLY"));
        }
    }
    for (search, total, lengths) in [
        ("D05_PAGING_ROW_", 86, vec![64, 22]),
        ("_MIRA", 44, vec![44]),
        ("D05_PAGING_ROW_043_MIRA", 2, vec![2]),
    ] {
        pages(
            &host,
            &session,
            &query(&child, 44, Observer::Player, View::History, None, search),
            total,
            &lengths,
        );
    }
    let first_query = query(&child, 44, Observer::Player, View::History, None, "");
    let first = host.inspection_query(&session, &first_query).unwrap();
    let mut second_query = first_query.clone();
    second_query.cursor = first.next_cursor.clone();
    let second = host.inspection_query(&session, &second_query).unwrap();
    assert_eq!(
        encoded(&host.inspection_query(&session, &first_query).unwrap()),
        encoded(&first)
    );
    assert_eq!(
        encoded(&host.inspection_query(&session, &second_query).unwrap()),
        encoded(&second)
    );
    wire(&host, json!({"op":"close","session":session,"scope":child}));
    drop(host);
    assert_eq!(fixture_oracle(&path).unwrap(), before);
}

#[test]
fn actual_knowledge_other_story_and_omni_to_actor_reads_do_not_change_canonical_or_actor_evidence()
{
    let path = copied_fixture();
    let before = fixture_oracle(&path).unwrap();
    let host = locallore_workspace::open(&path, true).unwrap();
    for (index, scope) in scopes().iter().enumerate() {
        let head = [0, 44, 1][index];
        let session = resume(&host, scope, head);
        for observer in [
            Observer::Player,
            Observer::Character { id: "mira".into() },
            Observer::Character { id: "sable".into() },
            Observer::Omniscient,
            Observer::Character { id: "mira".into() },
        ] {
            let page = host
                .inspection_query(
                    &session,
                    &query(scope, head, observer.clone(), View::Knowledge, None, ""),
                )
                .unwrap();
            assert!(page.next_cursor.is_none());
            let raw = String::from_utf8(encoded(&page)).unwrap();
            if index < 2 {
                assert!(
                    !raw.contains(OTHER_SECRET)
                        && !raw.contains(OTHER_MESSAGE)
                        && !raw.contains(AUTHOR_REASON)
                );
                match &observer {
                    Observer::Player => {
                        assert!(raw.contains(PLAYER_SECRET));
                        assert!(!raw.contains(MIRA_BELIEF) && !raw.contains(AUTHOR_TRUTH));
                    }
                    Observer::Character { id } if id == "mira" => {
                        assert!(raw.contains(MIRA_BELIEF));
                        for value in [PLAYER_SECRET, AUTHOR_TRUTH, "_PLAYER_ONLY"] {
                            assert!(!raw.contains(value));
                        }
                    }
                    Observer::Character { .. } => {
                        for value in [PLAYER_SECRET, MIRA_BELIEF, AUTHOR_TRUTH, "D05_PAGING_ROW_"] {
                            assert!(!raw.contains(value));
                        }
                    }
                    Observer::Omniscient => {
                        assert!(raw.contains(PLAYER_SECRET) && raw.contains(MIRA_BELIEF));
                        if index == 1 {
                            assert!(raw.contains(AUTHOR_TRUTH));
                        }
                    }
                }
            } else {
                for value in [
                    PLAYER_SECRET,
                    MIRA_BELIEF,
                    AUTHOR_TRUTH,
                    AUTHOR_REASON,
                    "D05_PAGING_ROW_",
                ] {
                    assert!(!raw.contains(value));
                }
                if matches!(observer, Observer::Player | Observer::Omniscient) {
                    assert!(raw.contains(OTHER_SECRET));
                }
                if matches!(&observer,Observer::Character{id} if id=="mira") {
                    assert!(!raw.contains(OTHER_SECRET) && raw.contains(OTHER_MESSAGE));
                }
            }
        }
        let totals = if index == 0 {
            [0, 0, 0, 0]
        } else if index == 2 {
            [3, 3, 1, 0]
        } else {
            [130, 129, 22, 0]
        };
        for (observer, total) in [
            Observer::Player,
            Observer::Omniscient,
            Observer::Character { id: "mira".into() },
            Observer::Character { id: "sable".into() },
        ]
        .into_iter()
        .zip(totals)
        {
            let page = host
                .inspection_query(
                    &session,
                    &query(scope, head, observer, View::History, None, ""),
                )
                .unwrap();
            assert_eq!(page.total, total);
        }
        wire(&host, json!({"op":"close","session":session,"scope":scope}));
    }
    drop(host);
    assert_eq!(fixture_oracle(&path).unwrap(), before);
    assert_eq!(actual_evidence(&path), before);
}

#[test]
fn production_workspace_host_grants_refuse_private_lenses_without_a_fake_persistence_adapter() {
    let path = copied_fixture();
    let before = fixture_oracle(&path).unwrap();
    let host = locallore_workspace::open(&path, false).unwrap();
    let child = scopes()[1].clone();
    let session = resume(&host, &child, 44);
    assert_eq!(
        host.inspection_query(
            &session,
            &query(&child, 44, Observer::Player, View::History, None, "")
        )
        .unwrap()
        .total,
        130
    );
    for observer in [
        Observer::Character { id: "mira".into() },
        Observer::Omniscient,
    ] {
        assert_eq!(
            host.inspection_query(
                &session,
                &query(&child, 44, observer, View::History, None, "")
            )
            .unwrap_err(),
            "Forbidden"
        );
    }
    // Query2 explicitly allows a Character lens naming the actual player without
    // a Lab grant. Do not freeze an incorrect blanket Character denial.
    assert_eq!(
        host.inspection_query(
            &session,
            &query(
                &child,
                44,
                Observer::Character {
                    id: "player".into()
                },
                View::History,
                None,
                ""
            )
        )
        .unwrap()
        .total,
        129
    );
    wire(&host, json!({"op":"close","session":session,"scope":child}));
    drop(host);
    assert_eq!(fixture_oracle(&path).unwrap(), before);
}

#[test]
fn actual_host_scope_head_observer_cursor_and_query_refusals_leave_all_evidence_unchanged() {
    let path = copied_fixture();
    let before = fixture_oracle(&path).unwrap();
    let host = locallore_workspace::open(&path, true).unwrap();
    let child = scopes()[1].clone();
    let session = resume(&host, &child, 44);
    let good = query(&child, 44, Observer::Player, View::History, None, "");
    let first = host.inspection_query(&session, &good).unwrap();
    let expected_first = encoded(&first.rows);
    let cursor = first.next_cursor.unwrap();
    let mut wrong = good.clone();
    wrong.scope = scopes()[2].clone();
    assert_eq!(
        host.inspection_query(&session, &wrong).unwrap_err(),
        "Scope"
    );
    let mut wrong = good.clone();
    wrong.expected_head = 43;
    assert_eq!(
        host.inspection_query(&session, &wrong).unwrap_err(),
        "Stale"
    );
    let mut wrong = good.clone();
    wrong.observer = Observer::Character {
        id: "missing-actor".into(),
    };
    assert_eq!(
        host.inspection_query(&session, &wrong).unwrap_err(),
        "UnknownObserver"
    );
    for (search, observer, at) in [
        ("_MIRA", Observer::Player, None),
        ("", Observer::Omniscient, None),
        ("", Observer::Player, Some(23)),
    ] {
        let mut wrong = query(&child, 44, observer, View::History, at, search);
        wrong.cursor = Some(cursor.clone());
        assert_eq!(
            host.inspection_query(&session, &wrong).unwrap_err(),
            "InvalidCursor"
        );
    }
    for value in ["bad".to_owned(), "2:0:bad".into(), "x".repeat(129)] {
        let mut wrong = good.clone();
        wrong.cursor = Some(value);
        assert_eq!(
            host.inspection_query(&session, &wrong).unwrap_err(),
            "InvalidCursor"
        );
    }
    for limit in [0, 65] {
        let mut wrong = good.clone();
        wrong.limit = limit;
        assert_eq!(
            host.inspection_query(&session, &wrong).unwrap_err(),
            "TooLarge"
        );
    }
    let mut wrong = good.clone();
    wrong.search = "x".repeat(257);
    assert_eq!(
        host.inspection_query(&session, &wrong).unwrap_err(),
        "TooLarge"
    );
    let mut wrong = good.clone();
    wrong.search = "\0".into();
    assert_eq!(
        host.inspection_query(&session, &wrong).unwrap_err(),
        "InvalidRequest"
    );
    let mut wrong = good.clone();
    wrong.at_revision = Some(45);
    assert_eq!(
        host.inspection_query(&session, &wrong).unwrap_err(),
        "InvalidBoundary"
    );
    for view in [View::Summaries, View::RetrievalIndexes] {
        let page = host
            .inspection_query(
                &session,
                &query(&child, 44, Observer::Player, view, None, ""),
            )
            .unwrap();
        assert_eq!(page.total, 0);
        assert!(page.rows.is_empty() && page.next_cursor.is_none());
        assert_eq!(
            serde_json::to_value(page.status).unwrap(),
            json!("unsupported")
        );
    }
    assert_eq!(
        encoded(&host.inspection_query(&session, &good).unwrap().rows),
        expected_first
    );
    wire(&host, json!({"op":"close","session":session,"scope":child}));
    drop(host);
    assert_eq!(fixture_oracle(&path).unwrap(), before);
}

#[test]
fn empty_store_and_one_isolated_extra_wait_are_refused_without_further_canonical_or_actor_change() {
    let empty = database(&packet());
    drop(Store::create_new_pinned(&empty).unwrap());
    assert_eq!(
        fixture_oracle(&empty).unwrap_err(),
        "SyntheticFixtureInvalid"
    );
    let mut store = Store::open_read_only(&empty).unwrap();
    assert!(store.stories().unwrap().is_empty());
    drop(store);
    let path = copied_fixture();
    let before = fixture_oracle(&path).unwrap();
    let child = scopes()[1].clone();
    let mut store = Store::open(&path, None).unwrap();
    let existing = store
        .lookup_author_correction(&correction(), &|| false)
        .unwrap()
        .unwrap();
    assert!(!existing.created);
    let engine = store.resume(&child).unwrap().engine;
    let request = engine.request(
        "d05-invalid-extra",
        Intent::Actions(vec![Command::Wait { ticks: 1 }]),
    );
    let proposal = Engine::proposal(&request).unwrap();
    let preview = engine.preview(&request, &proposal).unwrap();
    store.begin_turn(&request).unwrap();
    let committed = store.commit_prepared(&preview).unwrap();
    assert_eq!(committed.request(), &request);
    drop(store);
    let changed = actual_evidence(&path);
    assert_ne!(changed, before);
    assert_eq!(changed["scopes"][1]["head"], 45);
    assert_eq!(changed["scopes"][1]["story_time"], 101);
    assert_eq!(
        fixture_oracle(&path).unwrap_err(),
        "SyntheticFixtureInvalid"
    );
    assert_eq!(
        actual_evidence(&path),
        changed,
        "invalid fixture must not be repaired/rewound by oracle"
    );
    let mut store = Store::open_read_only(&path).unwrap();
    let saved = store.lookup_turn(&child, "d05-invalid-extra").unwrap();
    assert!(matches!(saved.phase, TurnPhase::Committed));
    assert_eq!(saved.receipt.unwrap().request(), &request);
}
