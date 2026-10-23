//! Explicit local development probe. Never logs prompts, paths or generated text.
use locallore_local_runtime::{Generation, LocalRuntime, Role};
use std::{
    path::Path,
    time::{Duration, Instant},
};
fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.len() != 3 {
        eprintln!("usage: runtime-probe <trusted-worker> <approved-model>");
        std::process::exit(2);
    }
    let result = (|| {
        let mut runtime =
            LocalRuntime::spawn_development(Path::new(&args[1]), Path::new(&args[2]))?;
        let load = runtime.load(|| false)?;
        let first=runtime.generate(Generation{role:Role::Director,prompt:"Return the JSON object {\"ok\":true}.".into(),schema:Some(serde_json::json!({"type":"object","properties":{"ok":{"type":"boolean"}},"required":["ok"],"additionalProperties":false})),max_tokens:64},||false)?;
        assert!(serde_json::from_str::<serde_json::Value>(&first.text).is_ok());
        let second = runtime.generate(
            Generation {
                role: Role::Narrator,
                prompt: "Describe rain on a stone quay in one short sentence.".into(),
                schema: None,
                max_tokens: 64,
            },
            || false,
        )?;
        assert!(!second.text.is_empty());
        assert_eq!(first.metrics.model_loads, 1);
        assert_eq!(second.metrics.model_loads, 1);
        assert_eq!(first.metrics.contexts_created, 1);
        assert_eq!(second.metrics.contexts_created, 2);
        let start = Instant::now();
        let cancellation = runtime.generate(
            Generation {
                role: Role::Narrator,
                prompt: "Write a long description of a rainy harbor, with every detail.".into(),
                schema: None,
                max_tokens: 350,
            },
            || start.elapsed() > Duration::from_millis(200),
        );
        assert_eq!(
            cancellation.as_ref().err(),
            Some(&locallore_local_runtime::Error::Cancelled)
        );
        let cancelled_ms = start.elapsed().as_millis();
        let cancel_metrics = runtime.last_metrics().cloned();
        let recovered = runtime.generate(
            Generation {
                role: Role::Narrator,
                prompt: "Say hello in three words.".into(),
                schema: None,
                max_tokens: 32,
            },
            || false,
        )?;
        assert!(!recovered.text.is_empty());
        runtime.unload()?;
        let reload = runtime.load(|| false)?;
        assert_eq!(reload.model_loads, 2);
        runtime.unload()?;
        runtime.shutdown()?;
        drop(runtime);
        let mut load_cancel =
            LocalRuntime::spawn_development(Path::new(&args[1]), Path::new(&args[2]))?;
        let cancel_load_start = Instant::now();
        assert_eq!(
            load_cancel
                .load(|| cancel_load_start.elapsed() > Duration::from_millis(20))
                .err(),
            Some(locallore_local_runtime::Error::Cancelled)
        );
        let load_cancel_ms = cancel_load_start.elapsed().as_millis();
        let load_cancel_metrics = load_cancel.last_metrics().cloned();
        assert!(load_cancel_metrics
            .as_ref()
            .is_some_and(|m| m.abort_callbacks > 0));
        drop(load_cancel);
        let mut fresh = LocalRuntime::spawn_development(Path::new(&args[1]), Path::new(&args[2]))?;
        let fresh_load = fresh.load(|| false)?;
        fresh.unload()?;
        fresh.shutdown()?;
        println!(
            "{}",
            serde_json::json!({"version":1,"status":"passed","load":load,"director":first.metrics,"narrator":second.metrics,"cancel_terminal_ms":cancelled_ms,"cancel_metrics":cancel_metrics,"recovery":recovered.metrics,"reload":reload,"load_cancel_ms":load_cancel_ms,"load_cancel_metrics":load_cancel_metrics,"fresh_load":fresh_load,"generated_text_saved":false})
        );
        Ok::<_, locallore_local_runtime::Error>(())
    })();
    if let Err(error) = result {
        println!("{}", serde_json::json!({"status":"error","category":error}));
        std::process::exit(1);
    }
}
