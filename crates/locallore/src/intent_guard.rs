//! Finite supported-English single-action input guard, not arbitrary NLP or mechanical rules.
//! Unknown IDs remain literal for Engine validation; no parser outcome establishes an effect.
use crate::{contracts::*, engine::Engine};

pub const INPUT_GUARD_VERSION: &str = "supported-english-v1";

fn word(actual: &str, expected: &str) -> bool {
    actual.eq_ignore_ascii_case(expected)
}
fn literal(value: &str) -> Result<String, Error> {
    if !value.is_empty()
        && value.len() <= 64
        && value
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b"-_".contains(&b))
    {
        Ok(value.into())
    } else {
        Err(Error::ClarificationRequired)
    }
}
fn number(value: &str) -> Option<u16> {
    if word(value, "one") {
        Some(1)
    } else {
        value
            .bytes()
            .all(|b| b.is_ascii_digit())
            .then(|| value.parse().ok())
            .flatten()
    }
}
fn article<'a>(words: &'a [&'a str]) -> &'a [&'a str] {
    if words
        .first()
        .is_some_and(|s| word(s, "my") || word(s, "the"))
    {
        &words[1..]
    } else {
        words
    }
}
fn item(words: &[&str]) -> Result<(String, u16), Error> {
    let words = if words.len() >= 2
        && word(words[0], "my")
        && (word(words[1], "last") || word(words[1], "sole"))
    {
        &words[2..]
    } else if words.first().is_some_and(|s| word(s, "another")) {
        &words[1..]
    } else {
        article(words)
    };
    match words {
        [id] => Ok((literal(id)?, 1)),
        [quantity, id] => Ok((
            literal(id)?,
            number(quantity).ok_or(Error::ClarificationRequired)?,
        )),
        _ => Err(Error::ClarificationRequired),
    }
}
fn ability(words: &[&str]) -> Result<String, Error> {
    let words = article(words);
    match words {
        [prefix, id] if word(prefix, "ability") => literal(id),
        [id, suffix] if word(suffix, "ability") => literal(id),
        [id] => literal(id),
        _ => Err(Error::ClarificationRequired),
    }
}
fn actor(engine: &Engine, words: &[&str]) -> Result<String, Error> {
    let reference = words.join(" ");
    // Canonical identifiers are exact and case-sensitive. Never normalize them into another ID.
    if engine.state().actors.contains_key(&reference) {
        return Ok(reference);
    }
    let player = &engine.state().actors[&engine.seed().player];
    let mut matches = engine.state().actors.iter().filter(|(_, a)| {
        a.alive && a.location == player.location && a.name.eq_ignore_ascii_case(&reference)
    });
    if let Some((id, _)) = matches.next() {
        if matches.next().is_some() {
            return Err(Error::ClarificationRequired);
        }
        return Ok(id.clone());
    }
    // This may be an unavailable explicit ID. Engine owns UnknownReference/Location decisions.
    literal(&reference)
}

/// Compile exactly one documented supported-English form. Unsupported syntax must be clarified;
/// it is never guessed into a different valid command. This function does not mutate the Engine.
pub fn compile_action(engine: &Engine, text: &str) -> Result<Command, Error> {
    if text.len() > MAX_TEXT_BYTES {
        return Err(Error::TooLarge);
    }
    if text.chars().any(|c| {
        c.is_control()
            || matches!(
                c,
                '\'' | '"' | '`' | '“' | '”' | '‘' | '’' | ';' | ',' | '&'
            )
    }) {
        return Err(Error::ClarificationRequired);
    }
    let text = text.trim();
    let text = text.strip_suffix('.').unwrap_or(text);
    let words = text.split_whitespace().collect::<Vec<_>>();
    if words.iter().any(|s| {
        [
            "and", "then", "or", "not", "never", "no", "but", "instead", "except",
        ]
        .iter()
        .any(|reserved| word(s, reserved))
    }) {
        return Err(Error::ClarificationRequired);
    }
    let words = if words.first().is_some_and(|s| word(s, "i")) {
        &words[1..]
    } else {
        &words[..]
    };
    let Some((verb, arguments)) = words.split_first() else {
        return Err(Error::ClarificationRequired);
    };
    if word(verb, "give") {
        let boundary = arguments
            .iter()
            .position(|s| word(s, "to"))
            .ok_or(Error::ClarificationRequired)?;
        let (item, quantity) = item(&arguments[..boundary])?;
        if arguments[boundary + 1..].is_empty() {
            return Err(Error::ClarificationRequired);
        }
        return Ok(Command::Give {
            item,
            to: actor(engine, &arguments[boundary + 1..])?,
            quantity,
        });
    }
    if word(verb, "consume") || word(verb, "drink") {
        let arguments = article(arguments);
        return match arguments {
            [id] => Ok(Command::Consume { item: literal(id)? }),
            _ => Err(Error::ClarificationRequired),
        };
    }
    if word(verb, "use") {
        return Ok(Command::UseAbility {
            ability: ability(arguments)?,
        });
    }
    if word(verb, "learn") {
        return Ok(Command::Learn {
            ability: ability(arguments)?,
        });
    }
    if word(verb, "move") || word(verb, "go") {
        let Some((prefix, rest)) = arguments.split_first() else {
            return Err(Error::ClarificationRequired);
        };
        if !word(prefix, "to") {
            return Err(Error::ClarificationRequired);
        }
        let rest = if rest.first().is_some_and(|s| word(s, "the")) {
            &rest[1..]
        } else {
            rest
        };
        return match rest {
            [id] => Ok(Command::Move { to: literal(id)? }),
            _ => Err(Error::ClarificationRequired),
        };
    }
    if word(verb, "wait") {
        let arguments = if arguments.first().is_some_and(|s| word(s, "for")) {
            &arguments[1..]
        } else {
            arguments
        };
        let Some((count, rest)) = arguments.split_first() else {
            return Err(Error::ClarificationRequired);
        };
        let ticks = number(count).ok_or(Error::ClarificationRequired)?;
        let rest = if rest.first().is_some_and(|s| word(s, "tide")) {
            &rest[1..]
        } else {
            rest
        };
        return match rest {
            [unit] if word(unit, "tick") || word(unit, "ticks") => Ok(Command::Wait { ticks }),
            _ => Err(Error::ClarificationRequired),
        };
    }
    if word(verb, "discover") {
        let arguments = if arguments.first().is_some_and(|s| word(s, "fact")) {
            &arguments[1..]
        } else {
            arguments
        };
        return match arguments {
            [id] => Ok(Command::Discover { fact: literal(id)? }),
            _ => Err(Error::ClarificationRequired),
        };
    }
    if word(verb, "believe") {
        let arguments = if arguments.first().is_some_and(|s| word(s, "claim")) {
            &arguments[1..]
        } else {
            arguments
        };
        let arguments = if arguments.first().is_some_and(|s| word(s, "event")) {
            &arguments[1..]
        } else {
            arguments
        };
        return match arguments {
            [id] if !id.is_empty() && id.bytes().all(|b| b.is_ascii_digit()) => {
                Ok(Command::Believe {
                    claim_event: id.parse().map_err(|_| Error::ClarificationRequired)?,
                })
            }
            _ => Err(Error::ClarificationRequired),
        };
    }
    Err(Error::ClarificationRequired)
}

/// Compare after the Engine's ordinary request/scope/head preflight. This guard binds intent,
/// while Engine resolution still owns ownership, abilities, references, locations and effects.
pub fn validate_action(
    engine: &Engine,
    request: &Request,
    proposal: &Proposal,
) -> Result<(), Error> {
    let Intent::FreeText {
        kind: PlayInputKind::Action,
        text,
    } = &request.intent
    else {
        return Err(Error::Agency);
    };
    let expected = compile_action(engine, text)?;
    if proposal.commands.as_slice() == [expected] {
        Ok(())
    } else {
        Err(Error::Agency)
    }
}
