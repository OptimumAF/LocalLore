//! Deliberately hostile process used only by development protocol tests.
use serde_json::json;
use std::io::{self, BufRead, Write};
fn main() {
    let mode = std::env::args()
        .nth(2)
        .and_then(|p| {
            std::path::Path::new(&p)
                .file_name()
                .map(|s| s.to_string_lossy().into_owned())
        })
        .unwrap_or_default();
    if mode == "no-read" {
        std::thread::sleep(std::time::Duration::from_secs(30));
        return;
    }
    for line in io::stdin().lock().lines() {
        let Ok(line) = line else { break };
        let Ok(req) = serde_json::from_str::<serde_json::Value>(&line) else {
            return;
        };
        if mode == "die" {
            return;
        }
        if mode == "hang" {
            std::thread::sleep(std::time::Duration::from_secs(30));
            return;
        }
        if mode == "overflow" {
            println!("{}", "x".repeat(70_000));
            return;
        }
        if mode == "stderr" {
            eprintln!("{}", "x".repeat(70_000));
            std::thread::sleep(std::time::Duration::from_secs(30));
            return;
        }
        let id = if mode == "wrong-id" {
            json!(99999)
        } else {
            req["id"].clone()
        };
        let mut reply = json!({"version":1,"id":id,"status":"completed","error":null,"text":"","metrics":{"load_ms":0,"prefill_ms":0,"decode_ms":0,"total_ms":0,"input_tokens":0,"output_tokens":0,"model_loads":1,"contexts_created":0,"abort_callbacks":0}}).to_string();
        if mode == "duplicate" {
            reply = reply.replacen("\"id\":", "\"id\":0,\"id\":", 1);
        }
        if mode == "truncated" {
            print!("{{");
            let _ = io::stdout().flush();
            return;
        }
        println!("{reply}");
        let _ = io::stdout().flush();
        if mode == "blocked-generation" {
            std::thread::sleep(std::time::Duration::from_secs(30));
            return;
        }
    }
}
