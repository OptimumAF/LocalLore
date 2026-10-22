# Security policy

## Current status

The project is at documentation-only bootstrap. There are no supported application releases and no completed security audit. Security design goals are not claims of verified protection.

## Reporting

Prefer GitHub's **Security → Advisories → Report a vulnerability** when private vulnerability reporting is visibly enabled for the official repository. Enabling and verifying it is a tracked setup task; this file alone does not enable it.

If that private action is not available, open a minimal issue asking the owner to establish a private reporting channel. Do not include exploit instructions, credentials, private saves, or affected users' information in the public issue. Do not send sensitive reports to an invented email address. The project makes no response-time guarantee at bootstrap.

A useful private report contains affected version/commit, a synthetic reproduction, expected versus actual behavior, impact, and relevant platform/runtime/model versions. Redact all personal content and unique device identifiers.

## Security priorities

Protect story data, local exports, native model parsers, import archives, repository automation, and release/signing credentials. Treat imported packs, model outputs, files, and retrieval content as untrusted. No model-generated command may invoke arbitrary code or access the filesystem/network. Validate archive paths and limits before extracting; reject executable story packs.

Models do not provide a security boundary. Prompt instructions supplement capability restrictions and validation; they do not replace them. Do not claim local inference protects against a compromised OS, a networked keyboard, a user-selected cloud export destination, or every operating-system backup behavior.

See `docs/PRIVACY_AND_THREAT_MODEL.md` and `docs/EVALUATION_AND_TESTING.md` for implementation requirements. Before a release, maintainers must declare supported versions, assess dependencies, define an update path, and verify the private reporting channel.
