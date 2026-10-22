//! Repair the pinned Rust 1.93.1 GNU response writer before invoking NDK Clang.
//! Its writer escapes spaces/backslashes, but leaves apostrophes active in GNU
//! syntax. Recover its newline-delimited arguments, then quote them correctly.

use std::ffi::OsString;
use std::fs::{self, OpenOptions};
use std::io::{self, Write};
use std::path::PathBuf;
use std::process::{self, Command};

fn decode_rust_argument(line: &str) -> io::Result<String> {
    let mut output = String::new();
    let mut characters = line.chars();
    while let Some(character) = characters.next() {
        if character == '\\' {
            match characters.next() {
                Some(escaped @ ('\\' | ' ')) => output.push(escaped),
                _ => {
                    return Err(io::Error::new(
                        io::ErrorKind::InvalidData,
                        "unexpected Rust response escape",
                    ))
                }
            }
        } else {
            output.push(character);
        }
    }
    Ok(output)
}

fn quote_gnu_argument(argument: &str) -> String {
    format!(
        "\"{}\"\n",
        argument.replace('\\', "\\\\").replace('"', "\\\"")
    )
}

#[derive(Default)]
struct RewrittenResponses(Vec<PathBuf>);

impl Drop for RewrittenResponses {
    fn drop(&mut self) {
        for path in &self.0 {
            let _ = fs::remove_file(path);
        }
    }
}

fn run() -> io::Result<i32> {
    let clang = std::env::var_os("LOCALLORE_ANDROID_CLANG").ok_or_else(|| {
        io::Error::new(
            io::ErrorKind::NotFound,
            "LOCALLORE_ANDROID_CLANG is required",
        )
    })?;
    let mut command = Command::new(clang);
    // Must be outside @files: Clang selects its tokenizer before expanding them.
    command.arg("--rsp-quoting=posix");
    let mut temporary = RewrittenResponses::default();
    for argument in std::env::args_os().skip(1) {
        if let Some(response) = argument.to_str().and_then(|value| value.strip_prefix('@')) {
            let source = PathBuf::from(response);
            let destination = source.with_extension(format!("locallore-{}.rsp", process::id()));
            let original = fs::read_to_string(&source)?;
            let mut corrected = OpenOptions::new()
                .write(true)
                .create_new(true)
                .open(&destination)?;
            temporary.0.push(destination.clone());
            for line in original.split_terminator('\n') {
                corrected.write_all(quote_gnu_argument(&decode_rust_argument(line)?).as_bytes())?;
            }
            drop(corrected);
            let mut response_argument = OsString::from("@");
            response_argument.push(destination);
            command.arg(response_argument);
        } else {
            command.arg(argument);
        }
    }
    Ok(command.status()?.code().unwrap_or(1))
}

fn main() {
    process::exit(match run() {
        Ok(code) => code,
        Err(error) => {
            eprintln!("LocalLore native linker: {error}");
            1
        }
    });
}

#[cfg(test)]
mod tests {
    use super::*;

    fn rust_response_escape(argument: &str) -> String {
        argument
            .chars()
            .fold(String::new(), |mut output, character| {
                if matches!(character, '\\' | ' ') {
                    output.push('\\');
                }
                output.push(character);
                output
            })
    }

    #[test]
    fn restores_actual_workspace_and_sdk_paths_without_losing_apostrophes() {
        for argument in [
            r"C:\Users\Avery\Documents\ChatGPT\The Hero's Journey\target\engine.o",
            r"C:\Program Files\Android\Sdk\lib.a",
            "C:/資料/hero's journey/engine.o",
            "-Wl,--version-script=C:/hero's journey/exports",
            "",
            r#"a\b\"quoted value"#,
        ] {
            assert_eq!(
                decode_rust_argument(&rust_response_escape(argument)).unwrap(),
                argument
            );
        }
    }

    #[test]
    fn gnu_response_quotes_apostrophes_and_escapes_double_quotes_and_backslashes() {
        assert_eq!(
            quote_gnu_argument(r#"C:\hero's "journey"\engine.o"#),
            "\"C:\\\\hero's \\\"journey\\\"\\\\engine.o\"\n"
        );
        assert_eq!(quote_gnu_argument(""), "\"\"\n");
    }

    #[test]
    fn rejects_unexpected_or_truncated_escape_instead_of_guessing() {
        assert!(decode_rust_argument("bad\\x").is_err());
        assert!(decode_rust_argument("bad\\").is_err());
    }
}
