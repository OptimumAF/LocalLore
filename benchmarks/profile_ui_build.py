"""Fixed B62 byte attestation; imports and manifest construction never publish.

Rehash the exact reviewed B62 bytes and current inputs. This is not a repeated
XML/DEX/ELF/aapt semantic review, nor historical process/tool re-attestation.
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

SCOPE = 'profile-ui-build-v1'
MODE = 'fixed-b62-byte-attestation-v1'
BASELINE_PATH = Path(__file__).with_name('profile_ui_build_baseline.json')
BASELINE_BYTES = 13217
BASELINE_SHA256 = 'b0572733b288cd272f0b5f21ba98399dd098082c5b2803ef6f150bcac7149e8c'
_FIXED = {'apks': {'product_apk': {'bytes': 28045456,
                          'path': 'D:\\Worktrees\\locallore-player-profile-core-v1\\apps\\android\\app\\build\\outputs\\apk\\debug\\app-debug.apk',
                          'sha256': '4129009f12f9bc21528c08afcd4d81ff56e8a96d8bc9cbb324b8130778f15a86'},
          'test_apk': {'bytes': 2336350,
                       'path': 'D:\\Worktrees\\locallore-player-profile-core-v1\\apps\\android\\app\\build\\outputs\\apk\\androidTest\\debug\\app-debug-androidTest.apk',
                       'sha256': '4935ef0df5b10a8dd718556c2d92a9b46d2b29c7ea4ece7eb287c3908117cba2'}},
 'capture': 'D:\\Dev\\Experiments\\LocalLore\\2026-11-01-player-self-profile-v1',
 'certificate': '17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564',
 'head': 'd687f5d560f61a704a91cbaf5c742cb7eac64996',
 'manifest': 'D:/Dev/Experiments/LocalLore/2026-11-01-profile-ui-harness-v1/profile-ui-build-v1.json',
 'recovery': 'D:\\Dev\\Recovery\\LocalLore\\2026-11-01-player-self-profile-v1',
 'root': 'D:\\Worktrees\\locallore-player-profile-core-v1',
 'source_count': 2561,
 'tested_count': 2560,
 'tested_head': 'b42a34f15d323ba2234aa3e4f125014af2a6163b'}
ROSTER = [['chat_ime_latest',
  'org.locallore.app.ui.ChatImeInsetsTest',
  'injectedImeKeepsLatestAboveOcclusionWithoutDoublePaddingSystemBars'],
 ['chat_ime_composer',
  'org.locallore.app.ui.ChatImeInsetsTest',
  'doubleFontComposerKeepsSendReachableAndDraftScopedAcrossInjectedImeChanges'],
 ['chat_status_history',
  'org.locallore.app.ui.ChatStatusAnnouncementTest',
  'historyReaderKeepsItsAnchorWhileCurrentBusyAndOutcomeAnnouncementsStayAvailable'],
 ['chat_status_draft',
  'org.locallore.app.ui.ChatStatusAnnouncementTest',
  'unicodeDialogueAndScopeStaySafeWhileEllipsizedNoticeKeepsFullSemantics'],
 ['chat_heading_selection',
  'org.locallore.app.ui.StoryHeadingScreenTest',
  'selectedAuthoredTitlesStayInsideTheIntroWhileDemoAndUnresolvedControlsRemainExact'],
 ['chat_heading_draft',
  'org.locallore.app.ui.StoryHeadingScreenTest',
  'titleRefreshRetainsDialogueButStoryAndBranchChangesFenceDraftsAndRetainedEdits'],
 ['chat_action_scope',
  'org.locallore.app.ui.QuickActionScopeScreenTest',
  'retainedStoryAndBranchClicksStayQuietWhileFreshControlsPreserveTheUnsentDialogue'],
 ['chat_action_availability',
  'org.locallore.app.ui.QuickActionScopeScreenTest',
  'persistentDemoAndWorkflowFencesDoNotTurnTextUnavailabilityIntoAnActionBlock'],
 ['inventory_entries',
  'org.locallore.app.ui.PlayerInventoryScreenTest',
  'savedRowsKnownEmptyAndUnavailableStayDistinctWhileDemoKeepsItsOriginalPotionRow'],
 ['inventory_scope',
  'org.locallore.app.ui.PlayerInventoryScreenTest',
  'scopeChangesFenceRetainedOpenAndCloseWhileAcceptedRefreshesKeepTheUnsentDialogue'],
 ['inventory_accessibility',
  'org.locallore.app.ui.PlayerInventoryScreenTest',
  'doubledFontKeepsLongExactIdentifiersAllQuantitiesAndCloseReachableWithoutGameActions'],
 ['profile_fields',
  'org.locallore.app.ui.PlayerSelfProfileScreenTest',
  'acceptedFieldsEmptyUnavailableAndNarrativeApplicabilityStaySeparateFromDemo'],
 ['profile_scope',
  'org.locallore.app.ui.PlayerSelfProfileScreenTest',
  'retainedInspectorCallbacksRespectScopesWorkflowClosureAndAcceptedRefreshWithoutSendingDraft'],
 ['profile_accessibility',
  'org.locallore.app.ui.PlayerSelfProfileScreenTest',
  'doubledFontKeepsFullUnicodeCollectionsAndCloseReachableWithoutCanonicalCallbacks']]
_FACTS = {'android_runtime_executed': False,
 'common_recorded_certificate': '17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564',
 'deep_semantic_review_repeated': False,
 'full_cache_or_TEMP_meter': False,
 'full_tool_binary_provenance': False,
 'jvm_cases': 454,
 'jvm_errors': 0,
 'jvm_failures': 0,
 'jvm_skips': 0,
 'jvm_suites': 55,
 'model_material': False,
 'old_b59_dex_review_reused': False,
 'recorded_new_profile_ui_methods_compiled': 3,
 'selected_runtime_methods': 14,
 'recorded_current_roster_junit_definitions': 14}
DOC_DELTA = ['README.md', 'docs/android/PLAYER_SELF_PROFILE_2026-11-01.md', 'docs/native/PLAYER_PRESENTATION_V2.md']
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
            for block in iter(lambda:stream.read(1024**2),b''):
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


def _paths():
    out,rec=Path(_FIXED['capture']),Path(_FIXED['recovery'])
    host=out/'host-build-v1'
    return dict(build=out/'closed-build-evidence-v1.json',before=host/'source-before-v1.json',
        after=host/'source-after-v1.json',tested_archive=host/'source-tested-v1.zip',
        final_source=out/'source-final-v1.json',final_archive=out/'source-final-v1.zip',
        preservation=rec/'recovery-receipt-v1.json',reviews=rec/'independent-final-readback-v1.json',
        build_review=out/'independent-build-readback-v1.json',request=host/'request-v1.json',
        actual_child=host/'actual-child-v1.json',owner=host/'owner-result-v1.json',terminal=host/'terminal-v1.json',
        public_start=host/'public-start-v1.json',public_child=host/'public-child-v1.json',
        public_terminal=host/'public-terminal-v1.json',
        dex=Path(_FIXED['manifest']).parent/'current-fourteen-dex-v1.json')


def _baseline(reader):
    pin=dict(path=str(BASELINE_PATH),bytes=BASELINE_BYTES,sha256=BASELINE_SHA256)
    value=reader.json(pin)
    _keys(value,('version','scope','product','refs','roster','facts','native','documentation_only_delta',
                 'preserved_controls','source_encoding','dex_inputs'))
    _need(type(value['version']) is int and value['version']==1 and value['scope']==MODE and
          _same(value['product'],_FIXED) and _same(value['facts'],_FACTS) and _same(value['roster'],ROSTER), 'baseline')
    _need(value['documentation_only_delta']==DOC_DELTA and value['source_encoding']==SOURCE_ENCODING, 'baseline')
    _keys(value['refs'],_paths())
    for key,path in _paths().items():
        _binding(value['refs'][key]);_need(Path(value['refs'][key]['path'])==path, 'baseline_path')
    return value,pin


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


def _source(reader,base,records):
    _need(_git(['rev-parse','HEAD']).decode('ascii').strip()==_FIXED['head'] and
          _git(['status','--porcelain','--untracked-files=all'])==b'', 'source')
    before,after,final=records['before'],records['after'],records['final_source']
    _need(_same(before,after) and before['head']==_FIXED['tested_head'] and
          final['head']==_FIXED['head'] and final['tested_head']==_FIXED['tested_head'] and
          final['worktree_clean'] is True and final['documentation_only_delta']==DOC_DELTA, 'source')
    current=_rows(final['files'],_FIXED['source_count']);old=_rows(before['files'],_FIXED['tested_count'])
    names=_git(['ls-files','-z']).decode('utf-8').split('\0')
    _need(names[-1]=='' and len(names[:-1])==len(set(names[:-1]))==len(current) and set(names[:-1])==set(current), 'source_roster')
    _need(sorted(k for k in old.keys()|current.keys() if old.get(k)!=current.get(k))==DOC_DELTA and
          set(current)-set(old)=={'docs/android/PLAYER_SELF_PROFILE_2026-11-01.md'} and not set(old)-set(current), 'source_delta')
    _need(_same(final['source_zip'],{k:base['refs']['final_archive'][k] for k in ('bytes','sha256')}), 'source_archive')
    # No canonical/LF normalization: current bytes must match recorded raw pins.
    for pin in current.values():reader.read(pin)


def _known_owner(value):
    return (type(value) is dict and value.get('status')=='child_exited' and
            type(value.get('worker_returncode')) is int and value['worker_returncode']==0 and
            value.get('cleanup_complete') is True and value.get('output_capture_complete') is True)


def _execution(reader,base,r):
    e=r['build'];terminal=r['terminal'];owner=r['owner'];request=r['request']
    _need(e['head']==_FIXED['tested_head'] and type(e['source_count']) is int and e['source_count']==_FIXED['tested_count'] and
          e['android_runtime_executed'] is False and e['full_cache_or_TEMP_meter'] is False, 'recorded_build')
    _need(_same(e['jvm']['counts'],dict(tests=454,failures=0,errors=0,skipped=0)) and
          type(e['jvm']['reports']) is list and len(e['jvm']['reports'])==55 and
          type(e['new_ui_methods_compiled']) is int and e['new_ui_methods_compiled']==3, 'recorded_tests')
    seen=set()
    for pin in e['jvm']['reports']:
        path=Path(pin['path']);_need(path not in seen and path.parent==Path(_FIXED['root'])/'apps/android/app/build/test-results/testDebugUnitTest', 'jvm')
        seen.add(path);reader.read(pin)
    reader.read(e['lint']['binding'])
    _need(_same(e['terminal'],terminal) and _same(e['public_terminal'],r['public_terminal']) and
          _same(terminal['owner'],owner) and _known_owner(owner) and terminal['passed'] is True and
          terminal['source_equal'] is True and terminal['meter_closed'] is True and terminal['faults']==[], 'owner')
    _need(type(r['public_terminal']['returncode']) is int and r['public_terminal']['returncode']==0 and
          request['head']==_FIXED['tested_head'] and type(request['seconds']) is int and request['seconds']==900 and
          _same(request['source_map'],base['refs']['before']), 'execution')
    actual,start,child=r['actual_child'],r['public_start'],r['public_child']
    _need(_same(actual['helper'],request['helper']) and _same(actual['identity'],start['worker']) and
          Path(start['cwd'])==Path(_FIXED['root']), 'execution_identity')
    for value in (actual['identity'],child['identity']):
        _need(type(value['pid']) is int and value['pid']>0 and type(value['creation_filetime']) is int and
              value['creation_filetime']>0 and type(value['executable']) is str, 'execution_identity')
    _need(actual['identity']['pid']!=child['identity']['pid'] and
          start['command']==child['command']==[actual['identity']['executable'],'-I','-S','-B','scripts/check.py','android','--offline'], 'execution_command')
    reader.read(request['helper'])
    for key in ('stdout','stderr'):
        _need(Path(e[key]['path'])==Path(_FIXED['capture'])/f'host-build-v1/owner-{key}-v1.bin' and
              type(owner[key+'_bytes']) is int and owner[key+'_bytes']==e[key]['bytes'], 'capture')
        reader.read(e[key])


def _retention(reader,base,r):
    receipt=r['preservation'];review=r['reviews'];build_review=r['build_review']
    _need(receipt['head']==review['head']==_FIXED['head'] and receipt['tested_head']==review['tested_head']==_FIXED['tested_head'] and
          receipt['originals_preserved'] is True and receipt['full_generated_backup'] is False and
          type(receipt['files']) is list and len(receipt['files'])==base['preserved_controls']['count'] and
          type(receipt['files_bytes']) is int and receipt['files_bytes']==base['preserved_controls']['bytes'], 'recovery')
    total=0;originals=set();copies=set()
    for row in receipt['files']:
        _keys(row,('original','copy','bytes','sha256'));p,q=Path(row['original']),Path(row['copy'])
        relative=p.relative_to(Path(_FIXED['capture']))
        _need(q==Path(_FIXED['recovery'])/'controls'/relative and p not in originals and q not in copies, 'recovery_path')
        originals.add(p);copies.add(q)
        for path in (p,q):reader.read(dict(path=str(path),bytes=row['bytes'],sha256=row['sha256']))
        total+=row['bytes']
    _need(total==receipt['files_bytes'] and review['passed'] is True and review['pair_original_copy_original_after'] is True and
          review['receipt_topology_exact'] is True and type(review['pair_count']) is int and review['pair_count']==len(originals) and
          review['source_current_raw_and_zip'] is True and review['source_count']==_FIXED['source_count'] and
          review['documentation_only_delta']==DOC_DELTA and _same(review['receipt'],base['refs']['preservation']), 'recovery_review')
    _need(build_review['blocking_findings']==[] and build_review['source_before_after_current_zip_equal'] is True and
          _same([build_review[k] for k in ('jvm_cases','jvm_xml','jvm_failures','jvm_errors','jvm_skipped','new_annotated_ui_methods')],
                [454,55,0,0,0,3]) and build_review['runtime_test_execution'] is False, 'build_review')


def _native(reader,base,r):
    rows=base['native'];_need(type(rows) is list and len(rows)==2 and _same(rows,r['build']['native']), 'native')
    root=Path(_FIXED['root'])/'apps/android/app/build'
    for row,(target,abi) in zip(rows,(('x86_64-linux-android','x86_64'),('aarch64-linux-android','arm64-v8a'))):
        paths=dict(release=root/f'rust-target/{target}/release/liblocallore_android.so',
            cargo_alias=root/f'rust-target/{target}/release/deps/liblocallore_android.so',
            generated=root/f'generated/rustJniLibs/{abi}/liblocallore_android.so',
            merged=root/f'intermediates/merged_native_libs/debug/mergeDebugNativeLibs/out/lib/{abi}/liblocallore_android.so',
            stripped=root/f'intermediates/stripped_native_libs/debug/stripDebugDebugSymbols/out/lib/{abi}/liblocallore_android.so')
        _need(row['abi']==abi and all(Path(row[k]['path'])==p for k,p in paths.items()), 'native_path')
        reader.native_pair(row['release'],row['cargo_alias'])
        for key in ('generated','merged','stripped'):reader.read(row[key])
        _need(len({row[k]['sha256'] for k in ('release','cargo_alias','generated','merged')})==1 and
              row['apk_sha256']==row['stripped']['sha256'], 'native_binding')


def _dex(reader,base,r):
    value=r['dex']
    _need(value['product_head']==_FIXED['head'] and value['tested_head']==_FIXED['tested_head'] and
          _same(value['app'],_FIXED['apks']['product_apk']) and _same(value['test'],_FIXED['apks']['test_apk']) and
          type(value['count']) is int and value['count']==14 and type(value['rows']) is list and len(value['rows'])==14 and
          value['new_and_previous_methods_checked_current_apk'] is True and value['device_runtime_or_aapt_execution'] is False and
          value['imports_before_external_operation_trap'] is True, 'dex_record')
    _keys(base['dex_inputs'],('contract','reader','dex_parser'))
    for key,pin in base['dex_inputs'].items():
        _need(_same(value[key],pin), 'dex_input');reader.read(pin)
    for row,selector in zip(value['rows'],ROSTER):
        _need([row['kind'],row['class'],row['method']]==selector and row['runtime_junit'] is True and
              row['public_concrete_instance_void_noargs'] is True and row['product_class_family_absent'] is True and
              type(row['code_units']) is int and 0<row['code_units']<=65536, 'dex_method')
        expected=Path(_FIXED['root'])/'apps/android/app/src/androidTest/java'/Path(*selector[1].split('.')).with_suffix('.kt')
        _need(Path(row['source']['path'])==expected, 'dex_source');reader.read(row['source'])


def _create_manifest():
    reader=_Reader();base,baseline_pin=_baseline(reader)
    archives=('tested_archive','final_archive')
    r={key:reader.json(pin) for key,pin in base['refs'].items() if key not in archives}
    for key in archives:reader.read(base['refs'][key])
    _source(reader,base,r);_execution(reader,base,r);_retention(reader,base,r);_native(reader,base,r);_dex(reader,base,r)
    _keys(r['build']['artifacts'],('product_apk','test_apk'))
    audits=r['build']['public_audits'];_need(type(audits) is list and len(audits)==2, 'audit')
    _keys(audits[0],('status','permissions','libraries'))
    _keys(audits[1],('app','test','certificate_sha256','package','status','test_package','test_permissions'))
    pair=audits[1]
    _need(audits[0]['status']==pair['status']=='passed' and pair['package']=='org.locallore.app' and
          pair['test_package']=='org.locallore.app.test' and pair['certificate_sha256']==_FIXED['certificate'], 'apk_policy')
    apks={}
    for role,pin in _FIXED['apks'].items():
        row=r['build']['artifacts'][role];_keys(row,('original','copy'))
        _need(_same(row['original'],pin) and _same({k:row['copy'][k] for k in ('bytes','sha256')},
              {k:pin[k] for k in ('bytes','sha256')}), 'apk_binding')
        reader.read(pin);reader.read(row['copy']);key='app' if role=='product_apk' else 'test'
        _need(_same(pair[key],{k:pin[k] for k in ('bytes','sha256')}), 'apk_binding')
        apks[role]=dict(binding=copy.deepcopy(pin),package='org.locallore.app'+('.test' if key=='test' else ''),
                        certificate_sha256=_FIXED['certificate'])
    _need(_git(['rev-parse','HEAD']).decode('ascii').strip()==_FIXED['head'] and
          _git(['status','--porcelain','--untracked-files=all'])==b'', 'source')
    reader.final()
    return dict(version=1,scope=SCOPE,validation_mode=MODE,baseline=baseline_pin,apks=apks,roster=copy.deepcopy(ROSTER),
        product_source=copy.deepcopy({k:_FIXED[k] for k in ('root','head','tested_head','source_count','tested_count')}),
        recorded_execution=dict(facts=copy.deepcopy(_FACTS),bindings=copy.deepcopy(base['refs']),
            documentation_only_delta=copy.deepcopy(DOC_DELTA),source_encoding=SOURCE_ENCODING),
        current_native_bindings=copy.deepcopy(base['native']))


def create_manifest():
    """Validate fixed B62 bytes and return data only; no publication or authority."""
    try:return _create_manifest()
    except BuildRefused:raise
    except (OSError,ValueError,KeyError,TypeError,IndexError,RecursionError,UnicodeError,subprocess.SubprocessError):
        raise BuildRefused('build') from None


def verify_frozen_product(artifacts):
    try:
        _keys(artifacts,('build','product_apk','test_apk'))
        for pin in artifacts.values():_binding(pin)
        _need(Path(artifacts['build']['path'])==Path(_FIXED['manifest']) and artifacts['build']['bytes']<=2*1024**2 and
              all(_same(artifacts[role],pin) for role,pin in _FIXED['apks'].items()), 'artifacts')
        reader=_Reader();actual=reader.json(artifacts['build']);expected=create_manifest()
        _need(_same(actual,expected), 'manifest')
        for role in _FIXED['apks']:reader.read(artifacts[role])
        reader.final();return copy.deepcopy(expected)
    except BuildRefused:raise
    except (OSError,ValueError,KeyError,TypeError,IndexError,RecursionError):
        raise BuildRefused('build') from None


def verify_current(admission):
    from benchmarks import owned_profile_ui_contract as contract
    value=contract.validate_admission(admission)
    contract.revalidate_inputs(value)
    result=verify_frozen_product(value['artifacts'])
    contract.revalidate_inputs(value)
    return result


