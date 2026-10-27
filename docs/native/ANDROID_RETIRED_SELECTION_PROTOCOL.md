# Retired selected-child saved-task oracle v1

M10.02/M05.05 lifecycle supporting, M08.05 retirement integration supporting
and M09.03 draft/notice preparation. Based on unmerged PR #199 at `12c70989`.
This is a bounded test contract, not an execution result, new production author
command, or complete branch-deletion qualification.

## Authority and fixed boundary

Retain the [root](ANDROID_PROCESS_RESTORATION_PROTOCOL.md) and
[active-child](ANDROID_CHILD_PROCESS_RESTORATION_PROTOCOL.md) cases and their
closed arguments, fixture rules,120s controller cap and ownership/saved-task
gates. The new create-only case is exactly `restore_retired_child`. It requires
the existing four arguments plus `fixture_test_sha256` (hex64); old cases still
require exactly their original four. There is no arbitrary package/path/action
argument and no retired-case reuse.

The controller pins the existing product/controller and the fixed product test
APK: debug identities, distinct UIDs, matching signing, one immutable base APK
each and exact hashes. Install all artifacts before creating the task. The new
fixture has the active-child's13 fields plus the test APK hash, under the fixed
private `process-controller-retired-v1` directory, scope
`locallore_retired_process_fixture_v1`. Original root/child fixture bytes and
schemas are unchanged.

The product UI creates A/B, a parent Dialogue atB1, and a child at1 through the
existing reviewed/consented fork. Enter the distinct unsent child draft. Save
the actual child task, require its newer after-super acknowledgement/STOPPED
state, kill only the fixed background product and verify the old PID is gone
and its final saved/commands vector is exactly `1,0,1,1,0,2` for
free_text/submit/prepare/commit/cancel/other. No child turn is sent.

## Test-only native fixture process

Only the test APK contains `RetiredSelectionFixtureMain` and its worker. No
manifest entry, production mutation hook, new JNI API, SQL, model or product
instrumentation is added. A separate `app_process` runs under the product UID;
it never starts an Activity or writes task/navigation state. The existing
NativeArchive typed preview/commit and Store stale-consent transaction remain
the retirement authority.

The bootstrap admits exactly two canonical, immutable `/data/app` APK classpath
entries (test then product), checks their hashes and expected package folders,
and uses public PathClassLoader with the exact product APK native path
`PRODUCT_APK!/lib/x86_64`. The product has `extractNativeLibs=false`; its STORED,
aligned native ZIP entry is used directly. No executable is extracted into app
data and no packaging/system setting changes. A child loader with a boot parent
loads the worker so the native search path belongs to the calling class loader.

Official [PathClassLoader documentation](https://developer.android.com/reference/dalvik/system/PathClassLoader)
defines its native search-path constructor; AOSP
[DexPathList](https://android.googlesource.com/platform/libcore/+/android12-release/dalvik/src/main/java/dalvik/system/DexPathList.java)
describes APK `!/` paths and uncompressed native entries.
[app_process source](https://android.googlesource.com/platform/frameworks/base.git/+/master/cmds/app_process/app_main.cpp)
describes the command-line main entry. These support the mechanism, not a claim
that this fixture has loaded successfully. Actual API35/x86_64 loading is a
mandatory gate before mutation; the ordinary product minimum remains26.

The helper takes exactly11 arguments:

```text
mode, run_id, expected_uid, product_sha256, test_sha256, native_path,
story_a, story_b, parent_branch, child_branch, saved_pid
```

All IDs/hex/numbers have closed native bounds. CWD must be the canonical fixed
product data directory and UID must match. The only admitted canonical homes
are `/data/user/0/PRODUCT` and `/data/data/PRODUCT`. Framework parents must be
real canonical directories; the only permitted intermediate alias is the exact
`/data/user/0` symlink to `/data/data`. The product leaf must be a nonlink owned
directory, with matching device/inode/UID through the named and canonical paths.
The test additionally binds its target ApplicationInfo data directory to this
same home. AOSP's [Zygote app-data mount setup](https://android.googlesource.com/platform/frameworks/base/+/master/core/jni/com_android_internal_os_Zygote.cpp)
explains why app and run-as processes can see different user-0 mappings; this
does not admit a supplied path, another package/user or arbitrary symlink.
`load` requires sentinel
load_a/load_b/main/load_child and saved_pid0; it invokes only
NativeArchive.close(0), opening no database. `probe`/`retire` require the actual
scope IDs, a disappeared positive saved PID, and the fixed private
`process-verify-v1/RUN/saved.json` matching nonce, UID, old identity, child hint
digest and exact setup vector. No supplied filesystem or database path is used.

Database/staging locations are fixed under that product's noBackup root.
Require an existing regular owned workspace and exactly the observed A0/B1/
child1 active catalog. The helper uses NativeArchive's existing typed
prepareBranchDelete request for this child/head1; validates scope/root/head,
empty retained descendants/heads, exactly the child removed and zero local
turns. `probe` closes without commit. `retire` writes a create-only intent marker
and consumes one fresh native prepared token exactly once. Require target
unavailability and A0/B1 preservation, exact child invalidation/one collected
leaf/zero deleted turns. Close every owned native handle before success. An
unknown mutation or close result is a failure; never retry/adopt that cohort.

Each helper has a15s watchdog, bounded4096-byte UTF-8 output and no raw exception,
path, SQL or player-text diagnostic. Success has exactly these18 keys:

```text
version=1, scope="locallore_retired_fixture_v1", mode, run_id,
status="passed", stage, pid, uid, started_uptime_ms,
product_sha256, test_sha256, library_sha256, scope_sha256,
commit_attempts, archive_closed, workspace_closed, before, after
```

Entry uptime is a helper entry observation, not a kernel process-start claim.
Stages are LOAD_COMPLETE/PROBE_CLOSED/RETIRED_CLOSED. Scope hash is UTF-8
`1\nA\nB\nparent\nchild\n`; the library hash covers the actual pinned ZIP entry.
Load has null before/after and0 commits. Otherwise each snapshot is exactly
`other_head,parent_head,target_head,target_active`: A0/B1/child1 active before;
probe unchanged; retired after has null target head/inactive and1 commit
attempt. Both close flags must be true. Failure is a separate closed six-key
version/scope/mode/run_id/statusfailed/stage shape, without exception text.

The controller merges helper/run-as stderr into stdout and preserves the exact
transport bytes before decoding or parsing. Create-only `MODE-transport-v1.bin`
leaves retain up to4160 bytes including both exit footers; `MODE-v1.json` retains
the original helper body after footer extraction, including its final LF. It
then requires the exact inner exit footer and0 before accepting proof or taking
another action. Extra VM/native chatter fails the single-JSON-line check. An
outer shell0 is not a helper success. Missing/contradictory/nonzero exit,
timeout or uncertain remote cleanup stops the case. Require each helper PID
gone and no product process before relaunching the task. Full original load/
probe/retire output is create-only under controller-private helpers-RUN leaves;
the result retains full probe/retire proofs and a load hash/identity summary,
plus retired-only last_helper_exit, reset to null before each dispatch. The
whole result remains4096 bytes. The existing shell caller's10s bound remains
stricter than the helper's15s watchdog; either timeout stops the case without a
dependent mutation or an implicit retry.

The helper command is a subshell group: its intentional exit0 enables the
unchanged generic outer footer, while its separately captured inner exit remains
authoritative. A top-level exit would suppress that outer footer and refuse the
case. The actual UiAutomation load gate must exercise both nested footers;
ProcessBuilder loading alone cannot qualify that transport.

Host readback of the opaque helper files must preserve bytes. On the verified
Windows path, scoped `adb exec-out run-as FIXED_CONTROLLER cat FIXED_LEAF`
preserves the device's LF bytes and proof hash. The retained `adb shell` copies
expanded LF to CRLF and failed comparison. Do not normalize those copies into
apparent success or relax the controller's quiet-LF gate. Bind every read to the
owned server/transport, fixed private leaf and existing output/client bounds.

## Restored fallback and second death

After qualified load/probe and one confirmed retirement, relaunch only the fixed
MainActivity with the existing launcher/NEW_TASK route. Require the same saved
task, new PID/start, factory1 and restored state. The original child hint must
resolve through fresh native catalogs to normal lexical A0, with the exact
notice: "Previously selected timeline is unavailable. Review the library before
sending." Require a blank composer, no child draft or parent receipt in A, and
zero automatic gameplay/create/fork attempts.

An explicit native reread consumes the one-shot notice. Save/stop/kill again and
restore the settled A0 task: blank composer, no repeated unavailable notice and
no resurrection of the retired hint/draft or automatic action. The second old
terminal gameplay vector is entirely zero. Explicitly inspect Broot1, its
unchanged accepted parent text and its root-only selectable timeline catalog;
return to A0 without cross-scope text. No force-stop/task clear or instrumentation
substitutes for either actual process death.

This tests a retired leaf between save and restore, not a real user's deletion
journey, retained-parent retirement, all missing/corrupt-storage cases, all API/
device combinations, power loss or model performance/quality. Supporting task
criteria and owner acceptance remain separate; no full milestone check-off.
