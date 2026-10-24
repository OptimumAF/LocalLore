// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Future native author port; frozen before production. UNCOMPILED/UNRUN.
//! Actual Store/Core/Host APIs; no SQL fixture writes, model or app execution.
use locallore::{
    author_correction::*,
    contracts::*,
    engine::{AcceptedHistoryBasis, Engine},
    host::{
        Host, NativeAuthorPreparation, Persistence, SavedTurn, WorkspaceAuthorOutcomeV1,
        WorkspaceSummary,
    },
    inspection_query::{Observer, Query, View},
};
use locallore_storage::{
    AuthorCorrectionOutcome, ForkRequest, PreparedStoreAuthorCorrection, Store,
};
use serde_json::{json, Value};
use std::{
    any::Any,
    cell::Cell,
    path::PathBuf,
    sync::{
        atomic::{AtomicBool, AtomicU64, Ordering},
        Arc,
    },
};

const A: &str = "PRIVATE_HOST_OLD_A";
const B: &str = "PRIVATE_HOST_NEW_B";
const REASON: &str = "PRIVATE_HOST_AUTHOR_REASON";
static NEXT: AtomicU64 = AtomicU64::new(0);
struct Fixture {
    directory: PathBuf,
    parent: Scope,
}
impl Fixture {
    fn new(value: &str) -> Self {
        let directory = std::env::temp_dir().join(format!(
            "locallore-native-author-{}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&directory).unwrap();
        let mut seed: Seed =
            serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
        let fact = seed.facts.get_mut("relic-location").unwrap();
        fact.proposition = value.into();
        fact.discoverable_at = Some("quay".into());
        fact.known_by.insert("mira".into());
        let parent = seed.scope.clone();
        let this = Self { directory, parent };
        this.store()
            .create_story("Synthetic native author", seed)
            .unwrap();
        this
    }
    fn path(&self) -> PathBuf {
        self.directory.join("synthetic.sqlite")
    }
    fn store(&self) -> Store {
        Store::open_application(&self.path()).unwrap()
    }
    fn host(&self, grant: bool) -> Host {
        locallore_workspace::open(&self.path(), grant).unwrap()
    }
    fn engine(&self, scope: &Scope) -> Engine {
        Store::open_read_only(&self.path())
            .unwrap()
            .resume(scope)
            .unwrap()
            .engine
    }
    fn lookup(&self, input: &AuthorCorrectionInputV1) -> Option<AuthorCorrectionOutcome> {
        Store::open_read_only(&self.path())
            .unwrap()
            .lookup_author_correction(input, &|| false)
            .unwrap()
    }
}
impl Drop for Fixture {
    fn drop(&mut self) {
        if let Err(error) = std::fs::remove_dir_all(&self.directory) {
            if !std::thread::panicking() {
                panic!("owned synthetic fixture cleanup failed: {error}");
            }
        }
    }
}
fn call(host: &Host, command: Value) -> Value {
    host.call(&serde_json::to_vec(&json!({"version":1,"command":command})).unwrap())
}
fn resume(host: &Host, scope: &Scope) -> String {
    let value = call(host, json!({"op":"resume","scope":scope}));
    assert_eq!(value["status"], "ok", "{value}");
    value["data"]["session"].as_str().unwrap().into()
}
fn correction_input(fixture: &Fixture, child: &str) -> AuthorCorrectionInputV1 {
    AuthorCorrectionInputV1 {
        version: 1,
        parent: fixture.parent.clone(),
        expected_parent_revision: 0,
        fork_revision: 0,
        child_branch: child.into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: "relic-location".into(),
            expected_proposition: A.into(),
            replacement: B.into(),
        },
        reason: REASON.into(),
    }
}
fn error<T>(result: Result<T, String>, expected: &str) {
    match result {
        Err(actual) => assert_eq!(actual, expected),
        Ok(_) => panic!("expected {expected}"),
    }
}
fn append(store: &mut Store, scope: &Scope, key: &str, commands: Vec<Command>) {
    let engine = store.resume(scope).unwrap().engine;
    let request = engine.request(key, Intent::Actions(commands));
    let proposal = Engine::proposal(&request).unwrap();
    let receipt = engine.preview(&request, &proposal).unwrap();
    store.begin_turn(&request).unwrap();
    store.commit_prepared(&receipt).unwrap();
}
fn wait(store: &mut Store, scope: &Scope, key: &str) {
    append(store, scope, key, vec![Command::Wait { ticks: 1 }]);
}
fn child(input: &AuthorCorrectionInputV1) -> Scope {
    Scope {
        story: input.parent.story.clone(),
        branch: input.child_branch.clone(),
    }
}

#[test]
fn prepare_is_actual_exact_private_preview_read_only_including_escaped_capacity() {
    for controls in [false, true] {
        let fixture = Fixture::new(A);
        let host = fixture.host(true);
        let session = resume(&host, &fixture.parent);
        let mut input = correction_input(&fixture, "preview");
        if controls {
            input.reason = "\u{1}".repeat(2048);
            let AuthorCorrectionOperationV1::ReplaceFactProposition { replacement, .. } =
                &mut input.operation;
            *replacement = "\u{2}".repeat(2048);
        }
        let parent = fixture.engine(&fixture.parent);
        let before = parent.accepted_history_basis().unwrap();
        let expected = parent.prepare_author_correction(&input, &|| false).unwrap();
        let preparation = host
            .prepare_author_correction(&session, &input, &|| false)
            .unwrap();
        assert_eq!(preparation.preview(), expected.preview());
        assert_eq!(
            preparation.preview_bytes(),
            serde_json::to_vec(expected.preview()).unwrap()
        );
        assert!(preparation.preview_bytes().len() <= MAX_RECEIPT_BYTES);
        if controls {
            assert!(preparation.preview_bytes().len() > locallore::host::MAX_INPUT);
        }
        assert_eq!(
            fixture
                .engine(&fixture.parent)
                .accepted_history_basis()
                .unwrap(),
            before
        );
        assert!(fixture.lookup(&input).is_none());
    }
}

#[test]
fn same_owner_commit_and_recorded_apply_ignore_true_or_panicking_cancel_without_extra_rows() {
    let fixture = Fixture::new(A);
    let host = fixture.host(true);
    let session = resume(&host, &fixture.parent);
    let input = correction_input(&fixture, "committed");
    let before = fixture
        .engine(&fixture.parent)
        .accepted_history_basis()
        .unwrap();
    let preparation = host
        .prepare_author_correction(&session, &input, &|| false)
        .unwrap();
    let outcome = host
        .apply_author_correction(&preparation, &|| false)
        .unwrap();
    assert_eq!(outcome.version, 1);
    assert!(outcome.created);
    assert_eq!(outcome.scope, child(&input));
    assert_eq!(outcome.parent, input.parent);
    assert_eq!(outcome.fork_revision, 0);
    assert_eq!(outcome.author_revision, 1);
    assert_eq!(outcome.head_revision, 1);
    let accepted = fixture.engine(&outcome.scope);
    let records = accepted.canonical_records().to_vec();
    assert_eq!(records.len(), 1);
    assert!(matches!(&records[0], CanonicalRecord::AuthorV1(record) if record.input() == &input));
    let calls = Cell::new(0);
    let retry = host
        .apply_author_correction(&preparation, &|| {
            calls.set(calls.get() + 1);
            true
        })
        .unwrap();
    assert!(!retry.created);
    assert_eq!(retry.scope, outcome.scope);
    assert_eq!(calls.get(), 0);
    let retry = host
        .apply_author_correction(&preparation, &|| {
            calls.set(calls.get() + 1);
            panic!("synthetic retry cancel")
        })
        .unwrap();
    assert!(!retry.created);
    assert_eq!(calls.get(), 0);
    assert_eq!(fixture.engine(&outcome.scope).canonical_records(), records);
    assert_eq!(
        fixture
            .engine(&fixture.parent)
            .accepted_history_basis()
            .unwrap(),
        before
    );
}

#[test]
fn native_grant_is_required_and_no_json_command_or_ephemeral_writer_is_added() {
    let fixture = Fixture::new(A);
    let ordinary = fixture.host(false);
    let session = resume(&ordinary, &fixture.parent);
    let input = correction_input(&fixture, "forbidden");
    error(
        ordinary.prepare_author_correction(&session, &input, &|| false),
        "Forbidden",
    );
    error(
        ordinary.lookup_author_correction(&input, &|| false),
        "Forbidden",
    );
    let granted = fixture.host(true);
    let granted_session = resume(&granted, &fixture.parent);
    let preparation = granted
        .prepare_author_correction(&granted_session, &input, &|| false)
        .unwrap();
    error(
        ordinary.apply_author_correction(&preparation, &|| false),
        "Forbidden",
    );
    let reply = call(
        &ordinary,
        json!({"op":"author_prepare","session":session,"input":input}),
    );
    assert_eq!(reply["error"], "Malformed");
    let ephemeral = Host::new(true);
    let created = call(&ephemeral, json!({"op":"create","seed":"lantern-quay-v1"}));
    let scope: Scope = serde_json::from_value(created["data"]["scope"].clone()).unwrap();
    let mut unsupported = input.clone();
    unsupported.parent = scope;
    error(
        ephemeral.prepare_author_correction(
            created["data"]["session"].as_str().unwrap(),
            &unsupported,
            &|| false,
        ),
        "Unsupported",
    );
    assert!(fixture.lookup(&input).is_none());
}

#[test]
fn foreign_reopened_and_closed_sessions_cannot_use_capabilities_even_for_recorded_results() {
    let fixture = Fixture::new(A);
    let host = fixture.host(true);
    let session = resume(&host, &fixture.parent);
    let input = correction_input(&fixture, "owner");
    let preparation = host
        .prepare_author_correction(&session, &input, &|| false)
        .unwrap();
    let foreign = fixture.host(true);
    resume(&foreign, &fixture.parent);
    error(
        foreign.apply_author_correction(&preparation, &|| false),
        "Integrity",
    );
    host.apply_author_correction(&preparation, &|| false)
        .unwrap();
    assert_eq!(
        call(
            &host,
            json!({"op":"close","session":session,"scope":fixture.parent})
        )["status"],
        "ok"
    );
    error(
        host.apply_author_correction(&preparation, &|| panic!("closed must fence before lookup")),
        "Closed",
    );
    drop(host);
    let reopened = fixture.host(true);
    resume(&reopened, &fixture.parent);
    error(
        reopened.apply_author_correction(&preparation, &|| false),
        "Integrity",
    );
    assert!(reopened
        .lookup_author_correction(&input, &|| false)
        .unwrap()
        .is_some());
}

#[test]
fn unknown_apply_and_prepare_cancel_or_panic_are_closed_and_leave_owner_usable() {
    let fixture = Fixture::new(A);
    let host = fixture.host(true);
    let session = resume(&host, &fixture.parent);
    let input = correction_input(&fixture, "cancelled");
    error(
        host.prepare_author_correction(&session, &input, &|| true),
        "Cancelled",
    );
    error(
        host.prepare_author_correction(&session, &input, &|| panic!("synthetic prepare cancel")),
        "Cancelled",
    );
    let preparation = host
        .prepare_author_correction(&session, &input, &|| false)
        .unwrap();
    error(
        host.apply_author_correction(&preparation, &|| true),
        "Cancelled",
    );
    error(
        host.apply_author_correction(&preparation, &|| panic!("synthetic apply cancel")),
        "Cancelled",
    );
    assert!(fixture.lookup(&input).is_none());
    assert!(
        host.apply_author_correction(&preparation, &|| false)
            .unwrap()
            .created
    );
    error(host.lookup_author_correction(&input, &|| true), "Cancelled");
    error(
        host.lookup_author_correction(&input, &|| panic!("synthetic explicit lookup cancel")),
        "Cancelled",
    );
    assert!(host
        .lookup_author_correction(&input, &|| false)
        .unwrap()
        .is_some());
}

#[test]
fn active_parent_work_blocks_fresh_prepare_and_apply_without_overwriting_its_key() {
    let fixture = Fixture::new(A);
    let host = fixture.host(true);
    let session = resume(&host, &fixture.parent);
    let input = correction_input(&fixture, "pending");
    let preparation = host
        .prepare_author_correction(&session, &input, &|| false)
        .unwrap();
    let request = fixture.engine(&fixture.parent).request(
        "original-pending-key",
        Intent::Actions(vec![Command::Wait { ticks: 1 }]),
    );
    let reply = call(
        &host,
        json!({"op":"submit","session":session,"request":request,"mode":"accepted"}),
    );
    assert_eq!(reply["data"]["phase"], "queued");
    error(
        host.prepare_author_correction(&session, &input, &|| false),
        "Busy",
    );
    error(
        host.apply_author_correction(&preparation, &|| false),
        "Busy",
    );
    assert!(fixture.lookup(&input).is_none());
    let cancelled = call(
        &host,
        json!({"op":"cancel","session":session,"scope":fixture.parent,"turn":request.turn}),
    );
    assert_eq!(cancelled["data"]["phase"], "cancelled");
    assert!(
        host.apply_author_correction(&preparation, &|| false)
            .unwrap()
            .created
    );
}

#[test]
fn actual_parent_append_invalidates_fresh_plan_but_not_exact_committed_lookup() {
    let fixture = Fixture::new(A);
    let host = fixture.host(true);
    let session = resume(&host, &fixture.parent);
    let input = correction_input(&fixture, "stale");
    let preparation = host
        .prepare_author_correction(&session, &input, &|| false)
        .unwrap();
    wait(&mut fixture.store(), &fixture.parent, "later-parent");
    error(
        host.apply_author_correction(&preparation, &|| false),
        "Stale",
    );
    assert!(fixture.lookup(&input).is_none());
    let mut fresh = input.clone();
    fresh.expected_parent_revision = 1;
    let preparation = host
        .prepare_author_correction(&session, &fresh, &|| false)
        .unwrap();
    let outcome = host
        .apply_author_correction(&preparation, &|| false)
        .unwrap();
    wait(&mut fixture.store(), &fixture.parent, "even-later-parent");
    assert!(
        !host
            .apply_author_correction(&preparation, &|| true)
            .unwrap()
            .created
    );
    assert_eq!(
        host.lookup_author_correction(&fresh, &|| false)
            .unwrap()
            .unwrap()
            .scope,
        outcome.scope
    );
}

#[test]
fn exact_lookup_preserves_full_input_kind_and_nonresurrection_semantics() {
    let fixture = Fixture::new(A);
    let host = fixture.host(true);
    let session = resume(&host, &fixture.parent);
    let input = correction_input(&fixture, "exact");
    let preparation = host
        .prepare_author_correction(&session, &input, &|| false)
        .unwrap();
    host.apply_author_correction(&preparation, &|| false)
        .unwrap();
    let mut mismatch = input.clone();
    mismatch.reason.push('!');
    error(
        host.lookup_author_correction(&mismatch, &|| false),
        "RetryMismatch",
    );
    let ordinary = correction_input(&fixture, "ordinary");
    fixture
        .store()
        .fork_branch(
            &ForkRequest {
                parent: fixture.parent.clone(),
                child_branch: ordinary.child_branch.clone(),
                expected_parent_revision: 0,
                at_revision: 0,
            },
            &|| false,
        )
        .unwrap();
    error(
        host.prepare_author_correction(&session, &ordinary, &|| false),
        "RetryMismatch",
    );
    error(
        host.lookup_author_correction(&ordinary, &|| false),
        "RetryMismatch",
    );
    let missing = correction_input(&fixture, "missing");
    assert!(host
        .lookup_author_correction(&missing, &|| false)
        .unwrap()
        .is_none());
    assert!(fixture.lookup(&missing).is_none());
}

#[test]
fn retained_child_lookup_and_recorded_apply_do_not_require_a_live_parent_creation_head() {
    let fixture = Fixture::new(A);
    let mut store = fixture.store();
    let parent = store
        .fork_branch(
            &ForkRequest {
                parent: fixture.parent.clone(),
                child_branch: "retained-parent".into(),
                expected_parent_revision: 0,
                at_revision: 0,
            },
            &|| false,
        )
        .unwrap()
        .scope;
    wait(&mut store, &parent, "excluded-parent-future");
    drop(store);
    let host = fixture.host(true);
    let session = resume(&host, &parent);
    let mut input = correction_input(&fixture, "retained-child");
    input.parent = parent.clone();
    input.expected_parent_revision = 1;
    let preparation = host
        .prepare_author_correction(&session, &input, &|| false)
        .unwrap();
    let outcome = host
        .apply_author_correction(&preparation, &|| false)
        .unwrap();
    let mut store = fixture.store();
    wait(&mut store, &parent, "more-excluded-future");
    let plan = store
        .prepare_branch_deletion(&parent, 2, &|| false)
        .unwrap();
    store.delete_branch(plan, &|| false).unwrap();
    assert!(store.resume(&parent).is_err());
    drop(store);
    assert_eq!(
        host.lookup_author_correction(&input, &|| false)
            .unwrap()
            .unwrap()
            .scope,
        outcome.scope
    );
    assert!(
        !host
            .apply_author_correction(&preparation, &|| panic!("recorded result bypasses cancel"))
            .unwrap()
            .created
    );
    let mut store = fixture.store();
    let plan = store
        .prepare_branch_deletion(&outcome.scope, 1, &|| false)
        .unwrap();
    store.delete_branch(plan, &|| false).unwrap();
    drop(store);
    error(host.lookup_author_correction(&input, &|| false), "NotFound");
}

#[test]
fn explicit_open_replacement_changes_session_work_owner_and_fences_old_preparation() {
    let fixture = Fixture::new(A);
    let host = fixture.host(true);
    let session = resume(&host, &fixture.parent);
    let input = correction_input(&fixture, "replaced");
    let preparation = host
        .prepare_author_correction(&session, &input, &|| false)
        .unwrap();
    let mut replacement = fixture.engine(&fixture.parent).seed().clone();
    replacement.facts.get_mut("ancestry").unwrap().proposition = "PRIVATE_REPLACED_SOURCE".into();
    let mut store = fixture.store();
    let plan = store
        .prepare_story_deletion(&fixture.parent, 0, &|| false)
        .unwrap();
    store.delete_story(plan, &|| false).unwrap();
    store
        .create_story("Synthetic replacement", replacement)
        .unwrap();
    drop(store);
    assert_eq!(
        call(
            &host,
            json!({"op":"open","session":session,"scope":fixture.parent})
        )["status"],
        "ok"
    );
    error(
        host.apply_author_correction(&preparation, &|| panic!("owner fence first")),
        "Stale",
    );
    assert!(fixture.lookup(&input).is_none());
}

// These test-only adapters still call actual Store APIs. One deterministically
// flips cancel AFTER the real commit; another returns a different actual Core
// source on resume, to make the post-prepare full-basis guard consequential.
struct StorePlan(PreparedStoreAuthorCorrection);
impl NativeAuthorPreparation for StorePlan {
    fn preview(&self) -> &AuthorCorrectionPreviewV1 {
        self.0.preview()
    }
    fn preview_bytes(&self) -> &[u8] {
        self.0.preview_bytes()
    }
    fn matches_parent_basis(&self, basis: &AcceptedHistoryBasis) -> bool {
        self.0.matches_parent_basis(basis)
    }
    fn as_any(&self) -> &dyn Any {
        self
    }
}
struct ProbePort {
    store: Store,
    selected_override: Option<Engine>,
    cancel_after_commit: Arc<AtomicBool>,
}
fn outcome(value: AuthorCorrectionOutcome) -> WorkspaceAuthorOutcomeV1 {
    WorkspaceAuthorOutcomeV1 {
        version: 1,
        scope: value.scope,
        parent: value.parent,
        fork_revision: value.fork_revision,
        author_revision: value.author_revision,
        head_revision: value.head_revision,
        created: value.created,
    }
}
impl Persistence for ProbePort {
    fn location(&self) -> &str {
        "synthetic-actual-store-probe"
    }
    fn list(&mut self) -> Result<Vec<WorkspaceSummary>, String> {
        Err("Unsupported".into())
    }
    fn create(&mut self) -> Result<Engine, String> {
        Err("Unsupported".into())
    }
    fn resume(&mut self, scope: &Scope) -> Result<Engine, String> {
        match &self.selected_override {
            Some(engine) => Ok(engine.clone()),
            None => self
                .store
                .resume(scope)
                .map(|snapshot| snapshot.engine)
                .map_err(|error| error.to_string()),
        }
    }
    fn prepare_author_correction(
        &mut self,
        input: &AuthorCorrectionInputV1,
        cancel: &dyn Fn() -> bool,
    ) -> Result<Box<dyn NativeAuthorPreparation>, String> {
        self.store
            .prepare_author_correction(input, cancel)
            .map(|plan| Box::new(StorePlan(plan)) as Box<dyn NativeAuthorPreparation>)
            .map_err(|error| error.to_string())
    }
    fn apply_author_correction(
        &mut self,
        preparation: &dyn NativeAuthorPreparation,
        cancel: &dyn Fn() -> bool,
    ) -> Result<WorkspaceAuthorOutcomeV1, String> {
        let plan = preparation
            .as_any()
            .downcast_ref::<StorePlan>()
            .ok_or("Integrity")?;
        let committed = self
            .store
            .apply_author_correction(&plan.0, cancel)
            .map_err(|error| error.to_string())?;
        self.cancel_after_commit.store(true, Ordering::SeqCst);
        Ok(outcome(committed))
    }
    fn lookup_author_correction(
        &mut self,
        input: &AuthorCorrectionInputV1,
        cancel: &dyn Fn() -> bool,
    ) -> Result<Option<WorkspaceAuthorOutcomeV1>, String> {
        self.store
            .lookup_author_correction(input, cancel)
            .map(|value| value.map(outcome))
            .map_err(|error| error.to_string())
    }
    fn begin(&mut self, _: &Request) -> Result<SavedTurn, String> {
        Err("Unsupported".into())
    }
    fn commit(&mut self, _: &Request, _: &Proposal, _: &str) -> Result<Receipt, String> {
        Err("Unsupported".into())
    }
    fn cancel(&mut self, _: &Request) -> Result<SavedTurn, String> {
        Err("Unsupported".into())
    }
    fn fail(&mut self, _: &Request) -> Result<SavedTurn, String> {
        Err("Unsupported".into())
    }
    fn stale(&mut self, _: &Request) -> Result<SavedTurn, String> {
        Err("Unsupported".into())
    }
    fn status(&mut self, _: &Scope, _: &str) -> Result<SavedTurn, String> {
        Err("Unsupported".into())
    }
}

#[test]
fn real_store_commit_return_wins_cancellation_that_arrives_after_commit() {
    let fixture = Fixture::new(A);
    let cancelled = Arc::new(AtomicBool::new(false));
    let host = Host::with_persistence(
        true,
        Box::new(ProbePort {
            store: fixture.store(),
            selected_override: None,
            cancel_after_commit: cancelled.clone(),
        }),
    );
    let session = resume(&host, &fixture.parent);
    let input = correction_input(&fixture, "late-cancel");
    let preparation = host
        .prepare_author_correction(&session, &input, &|| false)
        .unwrap();
    let committed = host
        .apply_author_correction(&preparation, &|| cancelled.load(Ordering::SeqCst))
        .unwrap();
    assert!(cancelled.load(Ordering::SeqCst));
    assert!(committed.created);
    assert!(fixture.lookup(&input).is_some());
}

#[test]
fn actual_store_prepared_basis_must_match_selected_full_source_before_preview_return() {
    let selected = Fixture::new(A);
    let actual = Fixture::new("PRIVATE_DIFFERENT_PARENT");
    let selected_engine = selected.engine(&selected.parent);
    let actual_engine = actual.engine(&actual.parent);
    assert_eq!(selected_engine.scope(), actual_engine.scope());
    assert_eq!(selected_engine.revision(), actual_engine.revision());
    assert_ne!(
        selected_engine.accepted_history_basis().unwrap(),
        actual_engine.accepted_history_basis().unwrap()
    );
    let mut input = correction_input(&actual, "wrong-source");
    let AuthorCorrectionOperationV1::ReplaceFactProposition {
        expected_proposition,
        ..
    } = &mut input.operation;
    *expected_proposition = "PRIVATE_DIFFERENT_PARENT".into();
    let plan = actual
        .store()
        .prepare_author_correction(&input, &|| false)
        .unwrap();
    assert!(plan.matches_parent_basis(&actual_engine.accepted_history_basis().unwrap()));
    assert!(!plan.matches_parent_basis(&selected_engine.accepted_history_basis().unwrap()));
    let host = Host::with_persistence(
        true,
        Box::new(ProbePort {
            store: actual.store(),
            selected_override: Some(selected_engine),
            cancel_after_commit: Arc::new(AtomicBool::new(false)),
        }),
    );
    let session = resume(&host, &actual.parent);
    error(
        host.prepare_author_correction(&session, &input, &|| false),
        "Stale",
    );
    assert!(actual.lookup(&input).is_none());
}

#[test]
fn private_author_preview_and_inspection_never_reteach_an_old_knower() {
    let fixture = Fixture::new(A);
    let host = fixture.host(true);
    let session = resume(&host, &fixture.parent);
    let input = correction_input(&fixture, "observations");
    let preparation = host
        .prepare_author_correction(&session, &input, &|| false)
        .unwrap();
    let committed = host
        .apply_author_correction(&preparation, &|| false)
        .unwrap();
    let child_session = resume(&host, &committed.scope);
    let query = Query {
        version: 2,
        scope: committed.scope.clone(),
        expected_head: 1,
        at_revision: None,
        observer: Observer::Character { id: "mira".into() },
        view: View::Knowledge,
        cursor: None,
        limit: 64,
        search: String::new(),
    };
    let before = fixture
        .engine(&committed.scope)
        .accepted_history_basis()
        .unwrap();
    let page =
        serde_json::to_string(&host.inspection_query(&child_session, &query).unwrap()).unwrap();
    assert!(page.contains(A));
    assert!(!page.contains(B));
    assert!(!page.contains(REASON));
    assert_eq!(
        fixture
            .engine(&committed.scope)
            .accepted_history_basis()
            .unwrap(),
        before
    );
    append(
        &mut fixture.store(),
        &committed.scope,
        "real-player-reobserve",
        vec![Command::Discover {
            fact: "relic-location".into(),
        }],
    );
    let engine = fixture.engine(&committed.scope);
    assert_eq!(
        engine.observed_facts("player", engine.scope(), 2).unwrap()["relic-location"].proposition,
        B
    );
    assert_eq!(
        engine.observed_facts("mira", engine.scope(), 2).unwrap()["relic-location"].proposition,
        A
    );
}
