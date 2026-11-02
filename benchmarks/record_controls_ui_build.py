"""Fixed B66 byte attestation. Import and manifest construction never publish.

This validates recorded byte/identity joins; it does not rerun XML/DEX/ELF/
signer tools, qualify Android, or attest all historical tool binaries.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import time

SCOPE = 'record-controls-ui-build-v1'
MODE = 'fixed-b66-byte-attestation-v1'
# This is recorded B66 data, not the location of the current implementation.
# Relocating a reader must not retag the immutable manifest's baseline identity.
BASELINE_PATH = Path('D:/Worktrees/locallore-record-controls-ui-core-v1/benchmarks/record_controls_ui_build_baseline.json')
BASELINE_BYTES = 16380
BASELINE_SHA256 = '2bcfa9dee3e8314e8fc24a10b9adec0481a31c165073c9bed9d6e54f138dc5fa'

_FIXED = {
    "root": "D:\\Worktrees\\locallore-record-actions-core-v1",
    "capture": "D:\\Dev\\Experiments\\LocalLore\\2026-11-01-promise-status-browse-v1",
    "recovery": "D:\\Dev\\Recovery\\LocalLore\\2026-11-01-promise-status-browse-v1",
    "manifest": "D:/Dev/Experiments/LocalLore/2026-11-01-record-controls-ui-harness-v1/record-controls-ui-build-v1.json",
    "head": "97d07f8923337f7e215d77f2f169ffd5cd4d2c1e",
    "tested_head": "62e9a50ab8a3734aa88bfebc220615a5241dfefe",
    "native_tested_head": "fa2ef2eb04b4e61626656e0c1993704b7fff520c",
    "previous_head": "0c5c7c7ba2048575248a7e7151043db03e43b901",
    "source_count": 2570,
    "tested_count": 2569,
    "certificate": "17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564",
    "apks": {
        "product_apk": {
            "path": "D:\\Worktrees\\locallore-record-actions-core-v1\\apps\\android\\app\\build\\outputs\\apk\\debug\\app-debug.apk",
            "bytes": 28329835,
            "sha256": "05813d21eb261fc694bd48485d5a5cb656206334577e4cdd543f703b558d66ad"
        },
        "test_apk": {
            "path": "D:\\Worktrees\\locallore-record-actions-core-v1\\apps\\android\\app\\build\\outputs\\apk\\androidTest\\debug\\app-debug-androidTest.apk",
            "bytes": 2456353,
            "sha256": "07d29a26ecf49060b7affc18b72d656559533fd947fffc42f88c53de71a3050a"
        }
    }
}
ROSTER = [
    [
        "chat_ime_latest",
        "org.locallore.app.ui.ChatImeInsetsTest",
        "injectedImeKeepsLatestAboveOcclusionWithoutDoublePaddingSystemBars"
    ],
    [
        "chat_ime_composer",
        "org.locallore.app.ui.ChatImeInsetsTest",
        "doubleFontComposerKeepsSendReachableAndDraftScopedAcrossInjectedImeChanges"
    ],
    [
        "chat_status_history",
        "org.locallore.app.ui.ChatStatusAnnouncementTest",
        "historyReaderKeepsItsAnchorWhileCurrentBusyAndOutcomeAnnouncementsStayAvailable"
    ],
    [
        "chat_status_draft",
        "org.locallore.app.ui.ChatStatusAnnouncementTest",
        "unicodeDialogueAndScopeStaySafeWhileEllipsizedNoticeKeepsFullSemantics"
    ],
    [
        "chat_heading_selection",
        "org.locallore.app.ui.StoryHeadingScreenTest",
        "selectedAuthoredTitlesStayInsideTheIntroWhileDemoAndUnresolvedControlsRemainExact"
    ],
    [
        "chat_heading_draft",
        "org.locallore.app.ui.StoryHeadingScreenTest",
        "titleRefreshRetainsDialogueButStoryAndBranchChangesFenceDraftsAndRetainedEdits"
    ],
    [
        "chat_action_scope",
        "org.locallore.app.ui.QuickActionScopeScreenTest",
        "retainedStoryAndBranchClicksStayQuietWhileFreshControlsPreserveTheUnsentDialogue"
    ],
    [
        "chat_action_availability",
        "org.locallore.app.ui.QuickActionScopeScreenTest",
        "persistentDemoAndWorkflowFencesDoNotTurnTextUnavailabilityIntoAnActionBlock"
    ],
    [
        "inventory_entries",
        "org.locallore.app.ui.PlayerInventoryScreenTest",
        "savedRowsKnownEmptyAndUnavailableStayDistinctWhileDemoKeepsItsOriginalPotionRow"
    ],
    [
        "inventory_scope",
        "org.locallore.app.ui.PlayerInventoryScreenTest",
        "scopeChangesFenceRetainedOpenAndCloseWhileAcceptedRefreshesKeepTheUnsentDialogue"
    ],
    [
        "inventory_accessibility",
        "org.locallore.app.ui.PlayerInventoryScreenTest",
        "doubledFontKeepsLongExactIdentifiersAllQuantitiesAndCloseReachableWithoutGameActions"
    ],
    [
        "profile_fields",
        "org.locallore.app.ui.PlayerSelfProfileScreenTest",
        "acceptedFieldsEmptyUnavailableAndNarrativeApplicabilityStaySeparateFromDemo"
    ],
    [
        "profile_scope",
        "org.locallore.app.ui.PlayerSelfProfileScreenTest",
        "retainedInspectorCallbacksRespectScopesWorkflowClosureAndAcceptedRefreshWithoutSendingDraft"
    ],
    [
        "profile_accessibility",
        "org.locallore.app.ui.PlayerSelfProfileScreenTest",
        "doubledFontKeepsFullUnicodeCollectionsAndCloseReachableWithoutCanonicalCallbacks"
    ],
    [
        "record_scope_story",
        "org.locallore.app.ui.StoryRecordActionScopeScreenTest",
        "retainedSearchNextAndCloseCannotRetargetAnotherStoryOrBranchAndFreshControlsStillWork"
    ],
    [
        "record_scope_reopen",
        "org.locallore.app.ui.StoryRecordActionScopeScreenTest",
        "equalValuedReopenAndLaterPagesRejectOldButtonsWithoutResettingTheCurrentDialogue"
    ],
    [
        "record_scope_detail",
        "org.locallore.app.ui.StoryRecordActionScopeScreenTest",
        "retainedListAndEventRetryBackAndSourceActionsCannotAffectFreshDetailsOrReopenedRecords"
    ],
    [
        "promise_status_browse",
        "org.locallore.app.ui.PromiseStatusScreenTest",
        "statusPagingAndEvidenceBackKeepTheNativePresetWhileTextSearchReturnsToAll"
    ],
    [
        "promise_status_scope",
        "org.locallore.app.ui.PromiseStatusScreenTest",
        "retainedPresetCannotRetargetLaterStatusEqualReopenOrAnotherStory"
    ]
]

_FACTS = dict(android_runtime_executed=False, model_material=False,
    deep_semantic_review_repeated=False, full_tool_binary_provenance=False,
    full_cache_or_TEMP_meter=False, jvm_cases=479, jvm_suites=58,
    jvm_failures=0, jvm_errors=0, jvm_skips=0, selected_runtime_methods=19,
    recorded_current_roster_junit_definitions=19, new_compiled_journeys=5,
    prior_exact_generated_xml_unrecoverable=57)
DOC_DELTA = ['README.md', 'docs/android/PROMISE_STATUS_BROWSING_2026-11-01.md',
             'docs/android/RECORD_QUERY2_CONTRACT_2026-10-31.md']
NATIVE_FIXTURE = 'crates/locallore/tests/m09_promise_status_search.rs'
SOURCE_ENCODING = 'Exact recorded raw worktree bytes; Git commit identity does not authorize newline normalization'

class BuildRefused(ValueError):
    """Fixed public refusal; no private file or captured output is disclosed."""


def _need(value, reason='build'):
    if not value:
        raise BuildRefused(reason)


def _keys(value, names):
    _need(type(value) is dict and set(value) == set(names), 'shape')


def _same(a, b):
    return json.dumps(a, sort_keys=True, allow_nan=False) == json.dumps(b, sort_keys=True, allow_nan=False)


def _json(raw):
    def unique(rows):
        result = {}
        for key, value in rows:
            _need(key not in result, 'json')
            result[key] = value
        return result
    return json.loads(raw.decode('utf-8-sig'), object_pairs_hook=unique,
        parse_constant=lambda _: (_ for _ in ()).throw(BuildRefused('json')))


def _binding(pin):
    _keys(pin, ('path','bytes','sha256'))
    _need(type(pin['path']) is str and type(pin['bytes']) is int and 0 <= pin['bytes'] <= 64*1024**2 and
          type(pin['sha256']) is str and re.fullmatch('[0-9a-f]{64}', pin['sha256']), 'binding')


def _relative(name):
    _need(type(name) is str and name and '\\' not in name and ':' not in name and
          not PurePosixPath(name).is_absolute() and all(p not in ('','.','..') for p in name.split('/')), 'path')


def _stamp(s):
    return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_mode,s.st_nlink)


class _Reader:
    """Bounded byte/identity checks only. No semantic parser or target/tool import."""
    def __init__(self):
        self.until = time.monotonic()+120
        self.checked = {}
        self.parents = {}
        self.total = 0
        root = Path(_FIXED['root'])/'apps/android/app/build/rust-target'
        self.cargo = tuple((root/target/'release/liblocallore_android.so',
                            root/target/'release/deps/liblocallore_android.so')
                           for target in ('x86_64-linux-android','aarch64-linux-android'))

    def info(self, path, cargo=False):
        _need(time.monotonic()<self.until and path.is_absolute() and path.drive.upper()=='D:', 'path')
        for parent in path.parents:
            if parent not in self.parents:
                s=parent.lstat()
                _need(stat.S_ISDIR(s.st_mode) and not stat.S_ISLNK(s.st_mode) and
                      not getattr(s,'st_file_attributes',0)&1024, 'path')
                self.parents[parent]=_stamp(s)
        s=path.lstat()
        _need(stat.S_ISREG(s.st_mode) and not stat.S_ISLNK(s.st_mode) and
              not getattr(s,'st_file_attributes',0)&1024 and s.st_nlink==(2 if cargo else 1), 'file')
        if cargo:
            _need(any(path in pair for pair in self.cargo), 'cargo_role')
        return s

    def read(self, pin, *, data=False, cargo=False):
        _binding(pin);path=Path(pin['path']);before=self.info(path,cargo)
        _need(before.st_size==pin['bytes'] and (not data or before.st_size<=2*1024**2), 'size')
        if not data and path in self.checked:
            old=self.checked[path]
            _need(old==(_stamp(before),pin,cargo), 'changed')
            return pin['sha256']
        h=hashlib.sha256();parts=[]
        with path.open('rb') as stream:
            held=os.fstat(stream.fileno())
            common=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_nlink,stat.S_IFMT(s.st_mode))
            _need(common(before)==common(held), 'identity')
            remaining=pin['bytes']+1
            while remaining:
                block=stream.read(min(1024**2,remaining))
                if not block:break
                remaining-=len(block)
                self.total+=len(block)
                _need(time.monotonic()<self.until and self.total<=512*1024**2, 'budget')
                h.update(block)
                if data:parts.append(block)
            _need(_stamp(held)==_stamp(os.fstat(stream.fileno())), 'changed')
        _need(h.hexdigest()==pin['sha256'] and _stamp(before)==_stamp(self.info(path,cargo)), 'changed')
        if path in self.checked:
            _need(self.checked[path]==(_stamp(before),pin,cargo), 'changed')
        self.checked[path]=(_stamp(before),copy.deepcopy(pin),cargo)
        return b''.join(parts) if data else pin['sha256']

    def json(self, pin):
        return _json(self.read(pin,data=True))

    def native_pair(self, release, alias):
        _need((Path(release['path']),Path(alias['path'])) in self.cargo, 'cargo_role')
        left,right=self.info(Path(release['path']),True),self.info(Path(alias['path']),True)
        _need((left.st_dev,left.st_ino,left.st_size,left.st_mtime_ns)==
              (right.st_dev,right.st_ino,right.st_size,right.st_mtime_ns), 'cargo_identity')
        _need(self.read(release,cargo=True)==self.read(alias,cargo=True), 'cargo_hash')

    def final(self):
        for path,(saved,pin,cargo) in self.checked.items():
            _need(_stamp(self.info(path,cargo))==saved, 'changed')
        for left,right in self.cargo:
            if left in self.checked or right in self.checked:
                a,b=self.info(left,True),self.info(right,True)
                _need((a.st_dev,a.st_ino)==(b.st_dev,b.st_ino), 'cargo_identity')
        for path,saved in self.parents.items():
            _need(_stamp(path.lstat())==saved, 'path_changed')



def _git(args):
    _need(args in (['rev-parse','HEAD'],['status','--porcelain','--untracked-files=all'],['ls-files','-z']), 'git')
    root=Path(_FIXED['root'])
    _need(root.drive.upper()=='D:' and root.resolve(strict=True)==root, 'path')
    for path in (root,*root.parents):
        s=path.lstat();_need(stat.S_ISDIR(s.st_mode) and not getattr(s,'st_file_attributes',0)&1024 and
                          not stat.S_ISLNK(s.st_mode), 'path')
    result=subprocess.run(['git','--no-optional-locks','-C',str(root)]+args,stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,timeout=15,env=dict(os.environ,GIT_OPTIONAL_LOCKS='0'))
    _need(result.returncode==0 and result.stderr==b'', 'source')
    return result.stdout


def _rows(rows,count):
    _need(type(rows) is list and len(rows)==count, 'source_roster')
    result={}
    for row in rows:
        _keys(row,('path','bytes','sha256'));_relative(row['path'])
        _need(row['path'] not in result, 'source_roster')
        pin=dict(row,path=str(Path(_FIXED['root'])/row['path']));_binding(pin)
        result[row['path']]=pin
    return result



def _paths():
    out, rec = Path(_FIXED['capture']), Path(_FIXED['recovery'])
    host, native = out/'android-v1', out/'native-v2'
    return dict(build=out/'closed-evidence-v1.json',
        before=host/'source-before-v1.json', after=host/'source-after-v1.json',
        native_before=native/'source-before-v1.json', native_after=native/'source-after-v1.json',
        tested_archive=host/'source-tested-v1.zip', native_archive=native/'source-tested-v1.zip',
        final_source=out/'source-final-v2.json', previous_source=out/'source-final-v1.json',
        preservation=rec/'recovery-receipt-v1.json', reviews=rec/'independent-final-readback-v1.json',
        addendum=rec/'preservation-addendum-v1.json', addendum_review=rec/'independent-addendum-readback-v1.json',
        build_review=out/'independent-evidence-readback-v1.json',
        request=host/'request-v1.json', actual_child=host/'actual-child-v1.json',
        command_child=host/'command-child-v1.json', command_terminal=host/'command-terminal-v1.json',
        owner=host/'owner-result-v1.json', terminal=host/'terminal-v1.json',
        helper=out/'run-check-v1.py', stdout=host/'owner-stdout-v1.bin', stderr=host/'owner-stderr-v1.bin',
        prior_limitation=out/'prior-generated-evidence-continuity-v1.json',
        current=Path(_FIXED['manifest']).parent/'current-nineteen-artifact-readback-v2.json')


def _baseline(reader):
    pin = dict(path=str(BASELINE_PATH), bytes=BASELINE_BYTES, sha256=BASELINE_SHA256)
    value = reader.json(pin)
    _keys(value, ('version','scope','product','refs','roster','facts','native','documentation_only_delta',
                  'preserved_controls','source_encoding','dex_inputs'))
    _need(type(value['version']) is int and value['version']==1 and value['scope']==MODE and
          _same(value['product'],_FIXED) and _same(value['facts'],_FACTS) and
          _same(value['roster'],ROSTER) and value['documentation_only_delta']==DOC_DELTA and
          value['source_encoding']==SOURCE_ENCODING, 'baseline')
    _keys(value['refs'],_paths())
    for key,path in _paths().items():
        _binding(value['refs'][key]); _need(Path(value['refs'][key]['path'])==path, 'baseline_path')
    return value,pin


def _source(reader, base, r):
    _need(_git(['rev-parse','HEAD']).decode('ascii').strip()==_FIXED['head'] and
          _git(['status','--porcelain','--untracked-files=all'])==b'', 'source')
    before, after, native, final = r['before'], r['after'], r['native_before'], r['final_source']
    _need(_same(before,after) and before['head']==_FIXED['tested_head'] and
          _same(native,r['native_after']) and native['head']==_FIXED['native_tested_head'] and
          final['head']==_FIXED['head'] and final['previous_final_head']==_FIXED['previous_head'] and
          final['production_unchanged'] is True and final['prior_snapshot_retained'] is True, 'source')
    old = _rows(before['files'],_FIXED['tested_count'])
    native_rows = _rows(native['files'],_FIXED['tested_count'])
    current = _rows(final['files'],_FIXED['source_count'])
    _need(set(old)==set(native_rows) and
          sorted(k for k in old if old[k]!=native_rows[k])==[NATIVE_FIXTURE], 'native_source_delta')
    _need(sorted(k for k in native_rows.keys()|current.keys() if native_rows.get(k)!=current.get(k))==DOC_DELTA and
          set(current)-set(native_rows)=={DOC_DELTA[1]} and not set(native_rows)-set(current), 'source_delta')
    names = _git(['ls-files','-z']).decode('utf-8').split('\0')
    _need(names[-1]=='' and len(names[:-1])==len(set(names[:-1]))==len(current) and set(names[:-1])==set(current), 'source_roster')
    _need(_same(final['tested_source_zip'],base['refs']['native_archive']), 'source_archive')
    overlays=final['documentation_only_delta']
    _need(type(overlays) is list and [row['path'] for row in overlays]==DOC_DELTA, 'source_overlay')
    for row in overlays:
        _keys(row,('path','copy','bytes','sha256'))
        _need(Path(row['copy'])==Path(_FIXED['capture'])/'final-docs-v2'/row['path'] and
              _same({k:row[k] for k in ('bytes','sha256')},
                    {k:current[row['path']][k] for k in ('bytes','sha256')}), 'source_overlay')
        reader.read(dict(path=row['copy'],bytes=row['bytes'],sha256=row['sha256']))
    for pin in current.values(): reader.read(pin)


def _known_owner(value):
    return (type(value) is dict and value.get('status')=='child_exited' and
            type(value.get('worker_returncode')) is int and value['worker_returncode']==0 and
            value.get('cleanup_complete') is True and value.get('output_capture_complete') is True)


def _identity(value):
    _keys(value,('pid','creation_filetime','executable'))
    _need(type(value['pid']) is int and value['pid']>0 and
          type(value['creation_filetime']) is int and value['creation_filetime']>0 and
          type(value['executable']) is str and value['executable'], 'execution_identity')


def _pair(reader, value, original, preserved):
    _keys(value,('original','copy'))
    _need(Path(value['original']['path'])==original and Path(value['copy']['path'])==preserved and
          _same({k:value['original'][k] for k in ('bytes','sha256')},
                {k:value['copy'][k] for k in ('bytes','sha256')}), 'copy_path')
    reader.read(value['original']); reader.read(value['copy'])


def _execution(reader, base, r):
    e, owner, terminal, request = r['build'], r['owner'], r['terminal'], r['request']
    _need(e['head']==_FIXED['native_tested_head'] and e['jvm_methods']==479 and type(e['jvm_methods']) is int and
          e['jvm_reports']==58 and type(e['jvm_reports']) is int and _same(e['jvm_failures_errors_skips'],[0,0,0]) and
          e['new_compose_executed'] is False and e['new_dependency_or_device_operation'] is False, 'recorded_tests')
    phase=e['phases']['android-v1']
    _need(phase['head']==_FIXED['tested_head'] and phase['source_count']==_FIXED['tested_count'] and
          _same(phase['owner'],owner) and _same(phase['terminal'],base['refs']['terminal']) and
          _same(terminal['owner'],owner) and _known_owner(owner) and terminal['passed'] is True and
          terminal['source_equal'] is True and terminal['faults']==[], 'owner')
    _need(type(r['command_terminal']['returncode']) is int and r['command_terminal']['returncode']==0 and
          request['head']==_FIXED['tested_head'] and Path(request['cwd'])==Path(_FIXED['root']) and
          type(request['seconds']) is int and request['seconds']==900 and
          _same(request['helper'],{k:base['refs']['helper'][k] for k in ('bytes','sha256')}), 'execution')
    actual, child = r['actual_child'], r['command_child']
    _need(_same(actual['helper'],request['helper']), 'execution_identity')
    for identity in (request['owner'],actual['identity'],child['identity']): _identity(identity)
    _need(len({request['owner']['pid'],actual['identity']['pid'],child['identity']['pid']})==3 and
          actual['identity']['executable']==request['owner']['executable']==child['identity']['executable'], 'execution_identity')
    command=[actual['identity']['executable'],'-I','-S','-B','scripts/check.py','android','--offline']
    _need(request['command']==child['command']==phase['command']==command, 'execution_command')
    reader.read(base['refs']['helper'])
    for key in ('stdout','stderr'):
        _need(type(owner[key+'_bytes']) is int and owner[key+'_bytes']==base['refs'][key]['bytes'], 'capture')
        reader.read(base['refs'][key])
    reports=e['reports']; _need(type(reports) is list and len(reports)==58, 'jvm')
    seen=set()
    for value in reports:
        original=Path(value['original']['path'])
        _need(original.parent==Path(_FIXED['root'])/'apps/android/app/build/test-results/testDebugUnitTest' and
              original.name.startswith('TEST-') and original.suffix=='.xml' and original not in seen, 'jvm')
        seen.add(original)
        _pair(reader,value,original,Path(_FIXED['capture'])/'reports-v1'/original.name)
    _pair(reader,e['lint'],Path(_FIXED['root'])/'apps/android/app/build/reports/lint-results-debug.xml',
          Path(_FIXED['capture'])/'reports-v1/lint-results-debug.xml')
    _need(e['lint_severities']=={'Warning':1,'Hint':1}, 'lint')
    cases=e['cases']
    _need(type(cases) is list and len(cases)==479 and all(type(row) is list and len(row)==2 and
          all(type(s) is str and s for s in row) for row in cases) and len({tuple(row) for row in cases})==479 and
          sum(row[0]=='org.locallore.app.PromiseStatusBrowseTest' for row in cases)==12, 'jvm_cases')
    review=r['build_review']
    _need(review['findings']==[] and review['jvm_unique_methods']==479 and review['jvm_xml_reports']==58 and
          _same(review['failures_errors_skips'],[0,0,0]) and review['report_original_copy_pairs_checked']==58 and
          review['android_production_source_unchanged'] is True and review['android_ui_executed'] is False and
          review['captured_signer_audit_matches_artifact_hashes'] is True and
          review['certificate_sha256']==_FIXED['certificate'], 'build_review')


def _retention(reader, base, r):
    receipt, addendum = r['preservation'], r['addendum']
    _need(receipt['head']==_FIXED['previous_head'] and receipt['source_count']==_FIXED['source_count'] and
          receipt['full_generated_cache_or_TEMP_backup'] is False and
          addendum['head']==_FIXED['head'] and addendum['prior_final_head']==_FIXED['previous_head'] and
          addendum['previous_109_pairs_and_apks_unchanged'] is True and addendum['source_count']==_FIXED['source_count'], 'recovery')
    originals, copies = set(), set()
    for name,record,subdir,count,bytes_key in (
            ('controls',receipt,'controls',109,'control_bytes'),
            ('addendum',addendum,'addendum-v1',8,'copied_bytes')):
        rows=record['files']
        expected=base['preserved_controls'][name]
        _need(type(rows) is list and len(rows)==count==expected['count'] and record['pair_count']==count and
              type(record[bytes_key]) is int and record[bytes_key]==expected['bytes'], 'recovery')
        total=0
        for row in rows:
            _keys(row,('original','copy','bytes','sha256'))
            original, preserved=Path(row['original']),Path(row['copy'])
            relative=original.relative_to(Path(_FIXED['capture']))
            _need(preserved==Path(_FIXED['recovery'])/subdir/relative and
                  original not in originals and preserved not in copies, 'recovery_path')
            originals.add(original);copies.add(preserved)
            for path in (original,preserved):reader.read(dict(path=str(path),bytes=row['bytes'],sha256=row['sha256']))
            total+=row['bytes']
        _need(total==record[bytes_key], 'recovery_bytes')
    review, last=r['reviews'],r['addendum_review']
    _need(review['head']==_FIXED['previous_head'] and review['findings']==[] and review['controls_verified']==109 and
          review['control_bytes']==receipt['control_bytes'] and review['artifacts_verified']==2 and
          review['source_files_verified']==_FIXED['source_count'] and
          _same(review['receipt'],base['refs']['preservation']), 'recovery_review')
    _need(last['head']==_FIXED['head'] and last['findings']==[] and
          last['new_original_copy_original_after_pairs']==8 and last['new_copied_bytes']==addendum['copied_bytes'] and
          last['all_2570_current_raw_source_and_zip_overlay_reconstruction_verified'] is True and
          last['same_native_v2_zip_crc_and_roster_verified'] is True and
          _same(last['addendum'],base['refs']['addendum']) and
          _same(last['prior_109_pair_receipt_unchanged'],{k:base['refs']['preservation'][k] for k in ('bytes','sha256')}) and
          _same(last['prior_independent_reader_unchanged'],{k:base['refs']['reviews'][k] for k in ('bytes','sha256')}), 'addendum_review')
    limitation=r['prior_limitation']
    _need(limitation['prior_packet']=='B65' and limitation['prior_xml_count']==57 and
          limitation['regenerated_xml_count']==57 and limitation['historical_capture_or_receipt_rewritten'] is False and
          last['report_explicitly_records_B65_final_57_XML_not_archived_or_recoverable'] is True, 'prior_limitation')


def _native(reader, base, r):
    rows=base['native']; _need(type(rows) is list and len(rows)==2, 'native')
    root=Path(_FIXED['root'])/'apps/android/app/build'
    current=r['current']['native']
    _need(type(current) is list and len(current)==2, 'native')
    for row,observed,(target,abi) in zip(rows,current,(('x86_64-linux-android','x86_64'),('aarch64-linux-android','arm64-v8a'))):
        paths=dict(release=root/f'rust-target/{target}/release/liblocallore_android.so',
            cargo_alias=root/f'rust-target/{target}/release/deps/liblocallore_android.so',
            generated=root/f'generated/rustJniLibs/{abi}/liblocallore_android.so',
            merged=root/f'intermediates/merged_native_libs/debug/mergeDebugNativeLibs/out/lib/{abi}/liblocallore_android.so',
            stripped=root/f'intermediates/stripped_native_libs/debug/stripDebugDebugSymbols/out/lib/{abi}/liblocallore_android.so')
        _need(row['abi']==observed['abi']==abi and all(Path(row[k]['path'])==p and
              _same(observed[k],row[k]) for k,p in paths.items()), 'native_path')
        reader.native_pair(row['release'],row['cargo_alias'])
        for key in ('generated','merged','stripped'): reader.read(row[key])
        _need(len({row[k]['sha256'] for k in ('release','cargo_alias','generated','merged')})==1 and
              observed['release_alias_links']==2 and row['apk_sha256']==observed['apk_sha256']==row['stripped']['sha256'], 'native_binding')


def _dex(reader, base, r):
    value=r['current']
    _need(value['scope']=='record-controls-ui-current-artifact-readback-v2' and
          value['product_head']==_FIXED['head'] and value['tested_head']==_FIXED['tested_head'] and
          value['native_tested_head']==_FIXED['native_tested_head'] and _same(value['apks'],_FIXED['apks']) and
          type(value['count']) is int and value['count']==19 and value['roster']==ROSTER and
          type(value['rows']) is list and len(value['rows'])==19 and value['runtime_execution'] is False and
          value['build_or_semantic_apk_ELF_signer_audit_repeated'] is False, 'dex_record')
    _keys(base['dex_inputs'],('contract','reader','dex_parser'))
    for key,pin in base['dex_inputs'].items():
        _need(_same(value[key],pin), 'dex_input'); reader.read(pin)
    for row,selector in zip(value['rows'],ROSTER):
        _need([row['kind'],row['class'],row['method']]==selector and row['runtime_junit'] is True and
              row['public_concrete_instance_void_noargs'] is True and row['product_class_family_absent'] is True and
              type(row['code_units']) is int and 0<row['code_units']<=8192, 'dex_method')
        expected=Path(_FIXED['root'])/'apps/android/app/src/androidTest/java'/Path(*selector[1].split('.')).with_suffix('.kt')
        _need(Path(row['source']['path'])==expected, 'dex_source'); reader.read(row['source'])


def _create_manifest():
    reader=_Reader(); base,baseline_pin=_baseline(reader)
    binary={'tested_archive','native_archive','helper','stdout','stderr'}
    r={key:reader.json(pin) for key,pin in base['refs'].items() if key not in binary}
    for key in binary: reader.read(base['refs'][key])
    _source(reader,base,r); _execution(reader,base,r); _retention(reader,base,r); _native(reader,base,r); _dex(reader,base,r)
    audits=r['build']['public_audits']; _need(type(audits) is list and len(audits)==2, 'audit')
    _keys(audits[0],('status','permissions','libraries'))
    _keys(audits[1],('app','test','certificate_sha256','package','status','test_package','test_permissions'))
    pair=audits[1]
    _need(audits[0]['status']==pair['status']=='passed' and len(audits[0]['libraries'])==4 and
          pair['package']=='org.locallore.app' and pair['test_package']=='org.locallore.app.test' and
          pair['certificate_sha256']==_FIXED['certificate'], 'apk_policy')
    apks={}
    for role,pin in _FIXED['apks'].items():
        key='app' if role=='product_apk' else 'test'
        _pair(reader,r['build']['artifacts'][key],Path(pin['path']),
              Path(_FIXED['recovery'])/'apks-v1'/Path(pin['path']).name)
        _need(_same(r['build']['artifacts'][key]['original'],pin) and
              _same(r['preservation']['artifacts'][key],r['build']['artifacts'][key]) and
              _same(pair[key],{k:pin[k] for k in ('bytes','sha256')}), 'apk_binding')
        apks[role]=dict(binding=copy.deepcopy(pin),package='org.locallore.app'+('.test' if key=='test' else ''),
                        certificate_sha256=_FIXED['certificate'])
    _need(_git(['rev-parse','HEAD']).decode('ascii').strip()==_FIXED['head'] and
          _git(['status','--porcelain','--untracked-files=all'])==b'', 'source')
    reader.final()
    return dict(version=1,scope=SCOPE,validation_mode=MODE,baseline=baseline_pin,apks=apks,roster=copy.deepcopy(ROSTER),
        product_source=copy.deepcopy({k:_FIXED[k] for k in ('root','head','tested_head','native_tested_head','source_count','tested_count')}),
        recorded_execution=dict(facts=copy.deepcopy(_FACTS),bindings=copy.deepcopy(base['refs']),
            documentation_only_delta=copy.deepcopy(DOC_DELTA),source_encoding=SOURCE_ENCODING),
        current_native_bindings=copy.deepcopy(base['native']))


def create_manifest():
    """Validate fixed B66 bytes; return data only, never publication or authority."""
    try: return _create_manifest()
    except BuildRefused: raise
    except (OSError,ValueError,KeyError,TypeError,IndexError,RecursionError,UnicodeError,subprocess.SubprocessError):
        raise BuildRefused('build') from None


def verify_frozen_product(artifacts):
    try:
        _keys(artifacts,('build','product_apk','test_apk'))
        for pin in artifacts.values(): _binding(pin)
        _need(Path(artifacts['build']['path'])==Path(_FIXED['manifest']) and artifacts['build']['bytes']<=2*1024**2 and
              all(_same(artifacts[role],pin) for role,pin in _FIXED['apks'].items()), 'artifacts')
        reader=_Reader(); actual=reader.json(artifacts['build']); expected=create_manifest()
        _need(_same(actual,expected), 'manifest')
        for role in _FIXED['apks']: reader.read(artifacts[role])
        reader.final(); return copy.deepcopy(expected)
    except BuildRefused: raise
    except (OSError,ValueError,KeyError,TypeError,IndexError,RecursionError):
        raise BuildRefused('build') from None


def verify_current(admission):
    from benchmarks import owned_record_controls_ui_contract as contract
    value=contract.validate_admission(admission)
    contract.revalidate_inputs(value)
    result=verify_frozen_product(value['artifacts'])
    contract.revalidate_inputs(value)
    return result
