# ADR-0002 — Bootstrap reporting routes and verified repository setup

Status: accepted as a bootstrap operational default under the owner's explicit delegation to finish GitHub and initial documents. Date: 2026-10-22. Related: M00.05, M00.06.

## Observation and decision

The original M00.06 wording required a private conduct contact, but the owner supplied no dedicated public contact address. Publishing a personal address or claiming a private inbox existed would be inappropriate. GitHub provides abuse-reporting tools and a Support contact form. Private vulnerability reporting is separately available and has been enabled for security reports.

Use GitHub's abuse tools/Support for sensitive abuse concerns, with clear limits in the conduct policy. Use nonsensitive issue/PR threads for project-owner attention, and request a private contact without evidence in public for other sensitive matters. Do not repurpose vulnerability reports as a general conduct inbox. A dedicated project-owner conduct inbox can be added later; none is claimed now.

M00.06 changes from “establish a private conduct contact” to “document a private conduct-reporting route.” This preserves a concrete nonpublic route for abuse reports without exposing personal contact data. GitHub handles its own policies; it does not promise to adjudicate every project disagreement. No enforcement authority or license is changed.

## Setup evidence

Active ruleset 25677641 was created after explicit owner approval. It requires pull requests, one code-owner approval, dismissal of stale reviews, conversation resolution, and no force pushes/deletion. The only bypass is OptimumAF in pull-request context. Settings and access details are recorded in PROJECT_STATUS and WORK_LOG. Existing account integrations were inventoried but not removed or given bypass.

The initial technical direction remains a revisable planning default. Physical-device/model benchmarks and all application work remain pending. Setup completion does not satisfy M01 or any app gate.

## Reference

[GitHub: Reporting abuse or spam](https://docs.github.com/en/communities/maintaining-your-safety-on-github/reporting-abuse-or-spam), checked 2026-10-22. No report or message was submitted during setup.
