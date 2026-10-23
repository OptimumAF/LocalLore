use locallore::inference::Cancellation;
use std::path::PathBuf;
fn main() {
    let args: Vec<_> = std::env::args().collect();
    if args.get(1).is_some_and(|s| s == "curated") {
        match locallore_eval::local_lane::cli(&args[2..]) {
            Ok(report) => {
                let failed = report
                    .cases
                    .iter()
                    .filter(|c| c.status == locallore_eval::Status::Failed)
                    .count();
                println!(
                    "{} stories={} failed={} completed={} quality_accepted=false",
                    report.lane,
                    report.cases.len(),
                    failed,
                    report.completed
                );
                if failed > 0 {
                    std::process::exit(1);
                }
            }
            Err(error) => {
                eprintln!("Evaluation failed: {error}");
                std::process::exit(2);
            }
        }
        return;
    }
    let usage="Usage: locallore-eval run|resume RUN_DIR [--max-cases 1..32] [--case BUILTIN_ID] | case NEW_RUN_DIR BUILTIN_ID";
    if args.len() < 3 || !matches!(args[1].as_str(), "run" | "resume" | "case") {
        eprintln!("{usage}");
        std::process::exit(2);
    }
    let mut selected = None;
    let mut max_cases = 32;
    if args[1] == "case" {
        if args.len() != 4 {
            eprintln!("{usage}");
            std::process::exit(2);
        }
        selected = Some(args[3].as_str());
    } else {
        let mut index = 3;
        while index < args.len() {
            if index + 1 >= args.len() {
                eprintln!("{usage}");
                std::process::exit(2);
            }
            match args[index].as_str() {
                "--case" if selected.is_none() => selected = Some(args[index + 1].as_str()),
                "--max-cases" => match args[index + 1].parse::<usize>() {
                    Ok(n) if (1..=32).contains(&n) => max_cases = n,
                    _ => {
                        eprintln!("{usage}");
                        std::process::exit(2);
                    }
                },
                _ => {
                    eprintln!("{usage}");
                    std::process::exit(2);
                }
            }
            index += 2;
        }
    }
    let result = locallore_eval::run_builtin(
        &PathBuf::from(&args[2]),
        args[1] == "resume",
        selected,
        &Cancellation::default(),
        max_cases,
    );
    match result {
        Ok(report) => {
            let failed = report
                .cases
                .iter()
                .filter(|c| c.status == locallore_eval::Status::Failed)
                .count();
            let unsupported = report
                .cases
                .iter()
                .filter(|c| c.status == locallore_eval::Status::Unsupported)
                .count();
            println!(
                "synthetic cases={} failed={} unsupported={} completed={} quality_accepted=false",
                report.cases.len(),
                failed,
                unsupported,
                report.completed
            );
            if failed > 0 {
                std::process::exit(1)
            }
        }
        Err(error) => {
            eprintln!("Evaluation failed: {error}");
            std::process::exit(2)
        }
    }
}
