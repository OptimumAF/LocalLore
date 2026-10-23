// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Explicit opt-in synthetic native-model + shared engine/store proof. No desktop UI/IPC.
use locallore::{
    contracts::*,
    engine::Engine,
    inference::{Cancellation, GenerationRequest, InferenceProvider, Input},
    play::{self, PlayProfile},
};
use locallore_local_runtime::{
    adapter::RuntimeProvider, LocalRuntime, MODEL_SHA256, PROFILE, RUNTIME_COMMIT,
};
use locallore_storage::Store;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{
    path::Path,
    sync::{Arc, Mutex},
    task::Poll,
    time::Instant,
};

struct RecordedProvider {
    inner: RuntimeProvider,
    outputs: Vec<Value>,
}
impl InferenceProvider for RecordedProvider {
    fn poll(
        &mut self,
        request: &GenerationRequest,
        cancel: &Cancellation,
    ) -> Poll<Result<Vec<u8>, Error>> {
        let result = self.inner.poll(request, cancel);
        if let Poll::Ready(Ok(bytes)) = &result {
            if let Input::Structured { role, .. } = &request.input {
                // Opt-in probe uses only this executable's fixed synthetic scenes.
                self.outputs
                    .push(json!({"role":role,"output":String::from_utf8_lossy(bytes)}));
            }
        }
        result
    }
}

fn scenario(
    store: &mut Store,
    runtime: Arc<Mutex<LocalRuntime>>,
    profile: &PlayProfile,
    scope: &Scope,
    turn: &str,
    input: (PlayInputKind, &str),
    cancel_after_ms: Option<u64>,
) -> Value {
    let (kind, text) = input;
    let engine = store.resume(scope).unwrap().engine;
    let request = engine.request(
        turn,
        Intent::FreeText {
            kind,
            text: text.into(),
        },
    );
    let before = engine.canonical_bytes();
    store.begin_turn(&request).unwrap();
    let cancel = Cancellation::default();
    let canceller = cancel_after_ms.map(|ms| {
        let token = cancel.clone();
        std::thread::spawn(move || {
            std::thread::sleep(std::time::Duration::from_millis(ms));
            token.cancel();
        })
    });
    let mut provider = RecordedProvider {
        inner: RuntimeProvider::new(runtime),
        outputs: vec![],
    };
    let mut candidate = engine.clone();
    let start = Instant::now();
    let result = play::execute(&mut candidate, &request, &mut provider, &cancel, profile);
    if let Some(c) = canceller {
        c.join().unwrap();
    }
    let metrics = provider.inner.metrics().cloned();
    let failure = provider.inner.last_failure();
    let outcome = match result {
        Ok(receipt) => match store.commit_prepared(&receipt) {
            Ok(committed) => {
                json!({"status":"committed","revision":candidate.revision(),"narration":committed.narration(),"fallback":committed.play().unwrap().fallback,"repairs":committed.play().unwrap().repairs,"stages":committed.play().unwrap().stages,"request_retained":committed.request()==&request})
            }
            Err(e) => json!({"status":"commit_failed","error":format!("{e:?}")}),
        },
        Err(e) => {
            if e == Error::Cancelled {
                let _ = store.cancel_turn(&request);
            } else {
                let _ = store.fail_turn(&request);
            }
            json!({"status":"rejected","error":e.to_string()})
        }
    };
    let current = store.resume(scope).unwrap().engine;
    json!({"scenario":turn,"kind":kind,"outcome":outcome,"synthetic_outputs":provider.outputs,"native_metrics_last_role":metrics,"runtime_error":failure,"total_ms":start.elapsed().as_millis(),"unchanged":current.canonical_bytes()==before,"head":current.revision(),"canonical_sha256":format!("{:x}",Sha256::digest(current.canonical_bytes()))})
}

fn main() {
    let args: Vec<_> = std::env::args_os().collect();
    assert_eq!(
        args.len(),
        3,
        "usage: play-scene-probe <trusted-packaged-resource-directory> <approved-existing-model>"
    );
    let resource = Path::new(&args[1]);
    let model = Path::new(&args[2]);
    let output = Path::new("target").join(format!(
        "d04-scene-{}",
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos()
    ));
    std::fs::create_dir_all(&output).unwrap();
    let overall = Instant::now();
    let mut runtime = LocalRuntime::spawn_packaged(resource, model)
        .expect("approved existing local profile required");
    let profile = PlayProfile {
        id: PROFILE.into(),
        model_sha256: MODEL_SHA256.into(),
        runtime_revision: RUNTIME_COMMIT.into(),
        template_sha256: "57f1fd00f0013a2be96aa79b857391f27e23df5b5f847072b524c897e24d0361".into(),
        worker_sha256: runtime.worker_sha256().into(),
        profile_manifest_sha256: runtime.profile_manifest_sha256(),
        context_tokens: 4096,
        director_tokens: 350,
        narrator_tokens: 220,
        deadline_ms: 120_000,
        repair_limit: 1,
    };
    let load = runtime.load(|| false).expect("local CPU load failed");
    let runtime = Arc::new(Mutex::new(runtime));
    let path = output.join("stories.sqlite");
    let mut store = Store::open(&path, None).unwrap();
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../../fixtures/lantern_quay.json")).unwrap();
    seed.scope.story = "real-synthetic-scene".into();
    let scope = seed.scope.clone();
    store.create_story("Synthetic local scene", seed).unwrap();
    let mut results = vec![];
    results.push(scenario(
        &mut store,
        runtime.clone(),
        &profile,
        &scope,
        "gift",
        (PlayInputKind::Action, "I give my last potion to Mira."),
        None,
    ));
    let after_gift = store.resume(&scope).unwrap().engine;
    let gift_committed =
        after_gift.revision() == 1 && after_gift.state().items["potion"].owner == "mira";
    drop(store);
    let mut store = Store::open(&path, None).unwrap();
    let restored = store.resume(&scope).unwrap().engine;
    let restarted_equal = restored.canonical_bytes() == after_gift.canonical_bytes();
    let original = after_gift.receipts().first().map(|r| r.request().clone());
    let exact_retry = original.as_ref().is_some_and(|r| {
        store.begin_turn(r).unwrap().receipt == after_gift.receipts().first().cloned()
    });
    results.push(scenario(
        &mut store,
        runtime.clone(),
        &profile,
        &scope,
        "second-potion",
        (PlayInputKind::Action, "I give another potion to Mira."),
        None,
    ));
    results.push(scenario(
        &mut store,
        runtime.clone(),
        &profile,
        &scope,
        "invented-power",
        (
            PlayInputKind::Action,
            "I use my teleport ability to jump to the tower.",
        ),
        None,
    ));
    results.push(scenario(
        &mut store,
        runtime.clone(),
        &profile,
        &scope,
        "secret",
        (
            PlayInputKind::Dialogue,
            "The tideglass relic lies in dry-well: SECRET-TIDE-731.",
        ),
        None,
    ));
    let current = store.resume(&scope).unwrap().engine;
    let mira = current
        .character_context("mira", &scope, current.revision())
        .unwrap();
    let sable = current
        .character_context("sable", &scope, current.revision())
        .unwrap();
    let speaker_scoped = serde_json::to_string(&mira)
        .unwrap()
        .contains("SECRET-TIDE-731")
        && !serde_json::to_string(&sable)
            .unwrap()
            .contains("SECRET-TIDE-731");
    results.push(scenario(
        &mut store,
        runtime.clone(),
        &profile,
        &scope,
        "cancel",
        (PlayInputKind::Action, "I wait for one tide tick."),
        Some(50),
    ));
    let final_engine = store.resume(&scope).unwrap().engine;
    let history: Vec<_> = final_engine
        .receipts()
        .iter()
        .map(|r| serde_json::to_string(r).unwrap())
        .collect();
    let replay_equal = Engine::restore(final_engine.seed().clone(), &history)
        .unwrap()
        .canonical_bytes()
        == final_engine.canonical_bytes();
    runtime.lock().unwrap().unload().unwrap();
    runtime.lock().unwrap().shutdown().unwrap();
    let scene_pass = gift_committed
        && restarted_equal
        && exact_retry
        && speaker_scoped
        && replay_equal
        && [1usize, 2, 4].iter().all(|&i| {
            results[i]["unchanged"] == true && results[i]["outcome"]["status"] == "rejected"
        })
        && results[4]["outcome"]["error"] == "Cancelled";
    let report = json!({"synthetic":true,"execution":"native CPU worker plus shared Rust engine/store; no desktop IPC or render","profile":profile,"load":load,"scene_pass":scene_pass,"gift_committed":gift_committed,"restart_equal":restarted_equal,"exact_retry_without_inference":exact_retry,"speaker_scoped_secret":speaker_scoped,"replay_without_inference":replay_equal,"results":results,"total_ms":overall.elapsed().as_millis(),"quality_accepted":false,"network_blocked":false});
    std::fs::write(
        output.join("report.json"),
        serde_json::to_vec_pretty(&report).unwrap(),
    )
    .unwrap();
    println!("{}", serde_json::to_string_pretty(&report).unwrap());
    if !scene_pass {
        std::process::exit(1);
    }
}
