//! Compile-time development-only stdio host for headless application rendering.
use locallore::{contracts::*, engine::Engine, host::Host, inference::*};
use serde_json::{json, Value};
use std::{
    io::{BufRead, Read, Write},
    sync::{
        atomic::{AtomicUsize, Ordering},
        Arc, Mutex,
    },
};

pub fn oracle(receipts: &Value) -> Value {
    let Some(rows) = receipts.as_array() else {
        return json!({"equal":false});
    };
    if rows.len() > 64 || serde_json::to_vec(rows).map_or(true, |b| b.len() > 262_144) {
        return json!({"equal":false});
    }
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../../fixtures/lantern_quay.json")).unwrap();
    if let Some(first) = rows.first() {
        let Ok(request) = serde_json::from_value::<Request>(first["request"].clone()) else {
            return json!({"equal":false});
        };
        seed.scope = request.scope;
    }
    let mut engine = Engine::new(seed).unwrap();
    for row in rows {
        let Ok(request) = serde_json::from_value::<Request>(row["request"].clone()) else {
            return json!({"equal":false});
        };
        let Ok(receipt) = execute(
            &mut engine,
            &request,
            &mut FakeProvider::new(FakeMode::Accepted),
            &Cancellation::default(),
            Budget::default(),
        ) else {
            return json!({"equal":false});
        };
        if serde_json::to_value(receipt).unwrap() != *row {
            return json!({"equal":false});
        }
    }
    json!({"equal":true,"revision":engine.revision(),"receipts":rows.len()})
}
pub fn run() {
    let host = Arc::new(Host::new(true));
    let output = Arc::new(Mutex::new(std::io::stdout()));
    let workers = Arc::new(AtomicUsize::new(0));
    let mut handles = vec![];
    let mut input = std::io::stdin().lock();
    for _ in 0..1024 {
        let mut bytes = vec![];
        let Ok(length) = input.by_ref().take(32_768).read_until(b'\n', &mut bytes) else {
            break;
        };
        if length == 0 {
            break;
        }
        if length >= 32_768 {
            break;
        }
        let Ok(message) = serde_json::from_slice::<Value>(&bytes) else {
            break;
        };
        let Some(id) = message["id"]
            .as_str()
            .filter(|s| s.len() <= 16)
            .map(str::to_owned)
        else {
            break;
        };
        let kind = message["kind"].as_str().unwrap_or("");
        let value = match kind {
            "oracle" => oracle(&message["receipts"]),
            "stats" => {
                let (sessions, workers) = host.live_counts();
                json!({"sessions":sessions,"workers":workers})
            }
            "host" => {
                let Some(payload) = message["input"]
                    .as_str()
                    .filter(|s| s.len() <= locallore::host::MAX_INPUT)
                else {
                    break;
                };
                let preparation = serde_json::from_str::<Value>(payload)
                    .ok()
                    .is_some_and(|v| v["command"]["op"] == "prepare");
                if preparation
                    && workers
                        .fetch_update(Ordering::SeqCst, Ordering::SeqCst, |n| {
                            (n < 4).then_some(n + 1)
                        })
                        .is_ok()
                {
                    let host = host.clone();
                    let output = output.clone();
                    let payload = payload.to_owned();
                    let workers = workers.clone();
                    handles.push(std::thread::spawn(move || {
                        reply(&output, &id, host.call(payload.as_bytes()));
                        workers.fetch_sub(1, Ordering::SeqCst);
                    }));
                    continue;
                }
                if preparation {
                    json!({"version":1,"status":"rejected","error":"Busy"})
                } else {
                    host.call(payload.as_bytes())
                }
            }
            _ => break,
        };
        reply(&output, &id, value);
    }
    host.close_all();
    for handle in handles {
        let _ = handle.join();
    }
}
fn reply(output: &Mutex<std::io::Stdout>, id: &str, value: Value) {
    if let Ok(mut out) = output.lock() {
        let _ = writeln!(out, "{}", json!({"id":id,"value":value}));
        let _ = out.flush();
    }
}
