# Licensing and contribution provenance

## First-party project material

The starter package uses **Apache License 2.0** for first-party code and documentation unless a file explicitly says otherwise. The complete license is in `../LICENSE`. This is the initial open-source choice prepared for the new project, not a claim that the owner previously selected it in conversation.

Apache-2.0 permits reuse, modification, and redistribution subject to its terms and includes an express patent license with conditions. It is permissive: it does not require every downstream modification to be published under the same license. Do not add a separate 'no commercial use' or 'no forks' restriction and still describe that result as the same open-source license. Read the actual license; this policy is not a substitute for legal advice. Reference [S13](REFERENCES.md).

The owner retains control over the official upstream repository and releases, not an unlimited power to revoke users' granted license rights. Contributors retain copyright in their contributions. Acceptance does not automatically assign ownership, authorize relicensing all contributors' work, or grant a maintainer role.

## Third-party material

Models, tokenizers, runtimes, assets, sample stories, and datasets retain their own applicable licenses. The application's license does not relicense an imported model. No weights or third-party story catalog are bundled in this starter package.

For every distributed dependency/artifact, record publisher/source, exact revision/hash, license identifier and text/notice location, redistribution obligations, modifications/conversion provenance, and distribution decision. A permissively licensed upstream model does not excuse an unverified third-party conversion or omitted notice. Prefer a baseline that can be built and used with open, redistributable dependencies; optional proprietary accelerators cannot be the only usable path.

Do not equate 'open weights' with a universal guarantee that a model meets every open-source definition or usage requirement. Verify each artifact at the time of selection. The research shortlist is not an approved redistribution inventory.

The Windows developer packager has a versioned, exact selected-dependency
[notice/source catalog](../licenses/desktop/catalog-v1.json). Its
[scoped audit evidence](desktop/D09_LICENSE_AUDIT_2026-10-23.md) distinguishes
mechanical material coverage from independent review and distribution approval.
The legacy `license_audit_complete` flag remains false. Included upstream MPL
source archives are public dependency source, separate from user stories and
model weights; the package still contains no weights. This implements inventory
checks under the policy above and does not change any applicable license.

## Contributions and generated material

Contributors submit only material they have rights to contribute, under Apache-2.0 for first-party changes unless agreed otherwise. There is no CLA or copyright-assignment requirement at bootstrap. Material AI assistance should be disclosed; it does not remove responsibility for provenance and review.

Use original synthetic fixtures. Do not copy another app's proprietary prompts, paid stories, branding, screenshots, or code into this project. Do not assert that all generated story output is copyrightable or automatically owned by the project; user-content/export terms need their own clear policy before release.

## Future changes

License changes require an owner-approved proposal and review of contributor/third-party rights. A governance vote or administrator permission alone does not establish legal permission to relicense others' contributions. Keep original notices and attribution when required.
