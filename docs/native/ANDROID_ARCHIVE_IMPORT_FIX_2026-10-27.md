# Archive import permission and passive reader fix

Refs #12 (M08.04/M08.06), #13 (M09.06), #14 (M10.02; supporting M10.03).
This follow-up is stacked on unmerged presentation PR #223 at `cf6d47d5`.
No merge is authorized; full task criteria and checkboxes remain unchanged.

## Original failures and changes

The preceding current850 retained-archive run executes both tests and fails
both assertions. Its [original report and verified private recovery](ANDROID_STORY_PRESENTATION_2026-10-27.md#subsequent-choice-pass-and-retained-archive-failures)
remain unchanged. The first observes WRITE permission on its selected import
URI. The second observes a rejected native resume, without its error category.

MainActivity now imports one openable content copy using the existing AndroidX
GetContent API and exact three MIME types. Consent, captured resolver, bounded
read, cancellation and native archive validation/commit remain unchanged.
The [platform's OpenDocument contract](https://developer.android.com/reference/android/content/Intent#ACTION_OPEN_DOCUMENT)
grants document read/write access; this app needs only one read. No new runtime,
dependency, storage permission or persisted grant is introduced.

The passive fixture previously resumed all catalog scopes through one native
Host, accumulating sessions beyond its four-session limit. Its rejection code
was not retained, so SessionLimit is a source-backed explanation rather than a
captured error label. Each passive branch snapshot now owns a dedicated Host
inside `use`; the catalog reader allocates no sessions. Shared `view` stays
unchanged because it can borrow an active gateway session. Engine limits stay
unchanged. Bounded operation/error diagnostics replace the uninformative status
assertion without dumping complete replies.

Both original methods and all canonical/receipt/revision/permission comparisons
remain. Added assertions check GET_CONTENT, OPENABLE, exact MIME filters and no
requested write/persistable/prefix flags. The actual negative source WRITE
assertion must still pass through DocumentsUI. Both methods run together, with
enough cumulative eligible scopes to exercise the original reader issue.

Android author commit `42a6d5e7` is integrated as `c5981788`. Root and an
independent adversarial reviewer inspect the three-file diff; no concrete source
defect is found. Source review and static checks do not establish runtime success.

## Verification status

Current-source host/build and fresh owned SDK qualification are pending. The
previous source's successful checks do not qualify this change. Original failed
evidence stays failed. No other emulator is stopped, system setting changed,
server restarted, private payload uploaded, or merge performed.
