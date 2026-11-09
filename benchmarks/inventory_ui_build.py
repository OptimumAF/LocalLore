"""Fixed B59 byte attestation; imports and manifest construction never publish.

Exact reviewed bytes retain their recorded semantic conclusions. This adapter
rehashes them and current inputs; it does not repeat XML/DEX/ELF/aapt semantics.
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

ROOT = Path(__file__).parents[1]
SCOPE = 'inventory-ui-build-v1'
MODE = 'fixed-b59-byte-attestation-v1'
BASELINE_PATH = Path(__file__).with_name('inventory_ui_build_baseline.json')
BASELINE_BYTES = 11641
BASELINE_SHA256 = '1e7da6ffd02639145d4aa32c6577ccd223ac2a942741f5934b4da826dd33e2be'
_FIXED = {'root': "D:\\Dev\\Projects\\The Hero's Journey\\LocalLore-spike-review",
 'head': 'ba548cbf6982c58d8a221aea2ed3606232d013d9',
 'tested_head': 'b8dbbcbb1b3ea67552d7449f94286187a31166ad',
 'source_count': 2549,
 'tested_count': 2548,
 'capture': 'D:\\Dev\\Experiments\\LocalLore\\2026-11-01-inventory-apks-v1',
 'recovery': 'D:\\Dev\\Recovery\\LocalLore\\2026-11-01-inventory-apks-v1',
 'manifest': 'D:/Dev/Experiments/LocalLore/2026-11-01-inventory-ui-cohort-v1/inventory-ui-build-v1.json',
 'apks': {'product_apk': {'path': "D:\\Dev\\Projects\\The Hero's "
                                  'Journey\\LocalLore-spike-review\\apps\\android\\app\\build\\outputs\\apk\\debug\\app-debug.apk',
                          'bytes': 28029072,
                          'sha256': '1806fd2594c09cccd8a79bb9c9608f55991f8f79bfe3f6d3f6a0f2660dab3683'},
          'test_apk': {'path': "D:\\Dev\\Projects\\The Hero's "
                               'Journey\\LocalLore-spike-review\\apps\\android\\app\\build\\outputs\\apk\\androidTest\\debug\\app-debug-androidTest.apk',
                       'bytes': 2321082,
                       'sha256': '6934df9326aa52353d7a15c5be0823c5227d916a3dcfcc2444feeade3ccece9d'}},
 'certificate': '17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564'}
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
  'doubledFontKeepsLongExactIdentifiersAllQuantitiesAndCloseReachableWithoutGameActions']]
_FACTS = {'jvm_cases': 439,
 'jvm_suites': 52,
 'jvm_failures': 0,
 'jvm_errors': 0,
 'jvm_skips': 0,
 'defined_junit_methods': 11,
 'aligned_libraries': 4,
 'native_chains': 2,
 'ordinary_profile': True,
 'model_material': False,
 'android_runtime_executed': False,
 'deep_semantic_review_repeated': False,
 'inner_aapt_raw_retained': False,
 'full_tool_binary_provenance': False,
 'common_recorded_certificate': '17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564'}


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
    return dict(build=out/'closed-build-evidence-v1.json',producer=out/'producer-closure-v1.json',
        preservation=rec/'preservation-receipt-v1.json',reviews=rec/'independent-readback-v1.json',
        final_source=out/'final-source-verification-v1.json',raw_pins=rec/'raw-source-pins-v1.json',
        before=out/'source-before-v1.json',after=out/'source-after-v1.json',
        tested_archive=out/'source-b8dbbcbb-v1.zip',canonical_archive=rec/'source-canonical-v1.zip',
        raw_archive=rec/'source-raw-v1.zip')


def _baseline(reader):
    pin=dict(path=str(BASELINE_PATH),bytes=BASELINE_BYTES,sha256=BASELINE_SHA256)
    value=reader.json(pin)
    _keys(value,('version','scope','product','refs','roster','facts','native','documentation_only_delta',
                 'raw_canonical_eol_paths','preserved_controls','producer_files'))
    _need(type(value['version']) is int and value['version']==1 and value['scope']==MODE and
          _same(value['product'],_FIXED) and _same(value['facts'],_FACTS) and
          _same(value['roster'],ROSTER), 'baseline')
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


def _source(reader, baseline, records):
    _need(_git(['rev-parse','HEAD']).decode('ascii').strip()==_FIXED['head'] and
          _git(['status','--porcelain','--untracked-files=all'])==b'', 'source')
    names=_git(['ls-files','-z']).decode('utf-8').split('\0')
    pins=records['raw_pins']
    _need(names[-1]=='' and len(names[:-1])==len(set(names[:-1]))==_FIXED['source_count'] and
          type(pins) is dict and set(names[:-1])==set(pins), 'source_roster')
    for name,pin in pins.items():
        _relative(name);_need(Path(pin['path'])==Path(_FIXED['root'])/name, 'source_path');reader.read(pin)
    before,after=records['before'],records['after']
    _need(_same(before,after) and before['head']==_FIXED['tested_head'] and
          type(before['files']) is list and len(before['files'])==_FIXED['tested_count'], 'tested_source')
    old={}
    for row in before['files']:
        _keys(row,('path','bytes','sha256'));_relative(row['path']);_need(row['path'] not in old, 'source_roster')
        old[row['path']]={k:row[k] for k in ('bytes','sha256')}
    current={name:{k:pin[k] for k in ('bytes','sha256')} for name,pin in pins.items()}
    changed=sorted(name for name in set(old)|set(current) if old.get(name)!=current.get(name))
    final=records['final_source']
    _need(changed==baseline['documentation_only_delta']==final['documentationOnlyDelta']==
          ['README.md','docs/android/PLAYER_INVENTORY_APKS_2026-11-01.md'] and
          set(current)-set(old)=={'docs/android/PLAYER_INVENTORY_APKS_2026-11-01.md'} and not set(old)-set(current), 'source_delta')
    _need(final['head']==_FIXED['head'] and final['testedHead']==_FIXED['tested_head'] and
          type(final['trackedFiles']) is int and final['trackedFiles']==_FIXED['source_count'] and
          _same(final['eolOnlyDifferences'],baseline['raw_canonical_eol_paths']) and
          _same(final['canonical'],baseline['refs']['canonical_archive']) and
          _same(final['raw'],baseline['refs']['raw_archive']), 'source_proof')


def _retention(reader, baseline, records):
    closure=records['producer'];pres=records['preservation'];build=records['build'];review=records['reviews']
    _need(closure['head']==_FIXED['tested_head'] and closure['closed_before_independent_review'] is True and
          closure['build_runs']==1 and closure['build_retries']==0 and closure['runtime_or_device_execution'] is False and
          type(closure['files']) is list and len(closure['files'])==baseline['producer_files'], 'producer')
    paths=set()
    for pin in closure['files']:
        path=Path(pin['path']);_need(path.is_relative_to(Path(_FIXED['capture'])) and path not in paths, 'producer_path')
        paths.add(path);reader.read(pin)
    _need(type(pres['controls']) is list and len(pres['controls'])==baseline['preserved_controls']['count'] and
          pres['controlsBytes']==baseline['preserved_controls']['bytes'] and
          _same(pres['source'],records['final_source']), 'preservation')
    total=0;originals=set();copies=set()
    for pair in pres['controls']:
        _keys(pair,('original','copy'));a,b=pair['original'],pair['copy'];p,q=Path(a['path']),Path(b['path'])
        name=p.relative_to(Path(_FIXED['capture']))
        _need(q==Path(_FIXED['recovery'])/'controls-v1'/name and p not in originals and q not in copies and
              a['bytes']==b['bytes'] and a['sha256']==b['sha256'], 'preservation_path')
        originals.add(p);copies.add(q);reader.read(a);reader.read(b);total+=a['bytes']
    _need(total==pres['controlsBytes'], 'preservation')
    _need(build['head']==_FIXED['tested_head'] and build['source_count']==_FIXED['tested_count'] and
          build['junit']['counts']==dict(tests=439,failures=0,errors=0,skipped=0) and
          build['junit']['unique_cases']==439 and build['junit']['xml_suites']==52 and
          build['android_runtime_executed'] is False and build['inner_aapt_raw_capture_claimed'] is False and
          build['full_tool_binary_provenance_claimed'] is False, 'recorded_build')
    _need(review['sourceHead']==_FIXED['head'] and review['testedHead']==_FIXED['tested_head'] and
          review['rolesClosed']==['native_build_policy','closed_apk_dex','final_preservation'] and
          review['artifactReader']['definedJUnitMethodsWithBodies']==11 and
          review['elevenAndroidMethodsUnrun'] is True, 'recorded_review')


def _native(reader, baseline):
    rows=baseline['native'];_need(type(rows) is list and len(rows)==2, 'native')
    base=Path(_FIXED['root'])/'apps/android/app/build'
    for row,(target,abi) in zip(rows,(('x86_64-linux-android','x86_64'),('aarch64-linux-android','arm64-v8a'))):
        paths=dict(release=base/f'rust-target/{target}/release/liblocallore_android.so',
            cargo_alias=base/f'rust-target/{target}/release/deps/liblocallore_android.so',
            generated=base/f'generated/rustJniLibs/{abi}/liblocallore_android.so',
            merged=base/f'intermediates/merged_native_libs/debug/mergeDebugNativeLibs/out/lib/{abi}/liblocallore_android.so',
            stripped=base/f'intermediates/stripped_native_libs/debug/stripDebugDebugSymbols/out/lib/{abi}/liblocallore_android.so')
        _need(row['abi']==abi and all(Path(row[k]['path'])==p for k,p in paths.items()), 'native_path')
        reader.native_pair(row['release'],row['cargo_alias'])
        for key in ('generated','merged','stripped'):reader.read(row[key])
        _need(len({row[k]['sha256'] for k in ('release','cargo_alias','generated','merged')})==1 and
              row['apk_sha256']==row['stripped']['sha256'] and row['release_alias_links']==2, 'native_binding')


def _create_manifest():
    reader=_Reader();baseline,baseline_pin=_baseline(reader)
    records={key:reader.json(pin) for key,pin in baseline['refs'].items()
             if key not in ('tested_archive','canonical_archive','raw_archive')}
    for key in ('tested_archive','canonical_archive','raw_archive'):reader.read(baseline['refs'][key])
    _source(reader,baseline,records);_retention(reader,baseline,records)
    _need(_same(records['build']['native'],baseline['native']), 'native_record')
    _native(reader,baseline)
    _need(type(records['build']['artifacts']) is list and len(records['build']['artifacts'])==55, 'artifacts')
    for row in records['build']['artifacts']:
        reader.read(row['original']);reader.read(row['copy'])
    pair=records['build']['pair_audit']
    _need(pair['package']=='org.locallore.app' and pair['test_package']=='org.locallore.app.test' and
          pair['certificate_sha256']==_FIXED['certificate'] and pair['status']=='passed', 'apk_policy')
    apks={}
    for role,pin in _FIXED['apks'].items():
        reader.read(pin);key='app' if role=='product_apk' else 'test'
        _need(_same(pair[key],{k:pin[k] for k in ('bytes','sha256')}), 'apk_binding')
        apks[role]=dict(binding=copy.deepcopy(pin),package='org.locallore.app'+('.test' if key=='test' else ''),
                        certificate_sha256=_FIXED['certificate'])
    _need(_git(['rev-parse','HEAD']).decode('ascii').strip()==_FIXED['head'] and
          _git(['status','--porcelain','--untracked-files=all'])==b'', 'source')
    reader.final()
    return dict(version=1,scope=SCOPE,validation_mode=MODE,baseline=baseline_pin,apks=apks,roster=copy.deepcopy(ROSTER),
        product_source=copy.deepcopy({k:_FIXED[k] for k in ('root','head','tested_head','source_count','tested_count')}),
        recorded_execution=dict(facts=copy.deepcopy(_FACTS),bindings=copy.deepcopy(baseline['refs']),
            documentation_only_delta=copy.deepcopy(baseline['documentation_only_delta']),
            raw_canonical_eol_paths=copy.deepcopy(baseline['raw_canonical_eol_paths'])),
        current_native_bindings=copy.deepcopy(baseline['native']))


def create_manifest():
    """Pure fixed-B59 byte validation; return data only, never create a manifest."""
    try:
        return _create_manifest()
    except BuildRefused:
        raise
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
    except BuildRefused:
        raise
    except (OSError,ValueError,KeyError,TypeError,IndexError,RecursionError):
        raise BuildRefused('build') from None


def verify_current(admission):
    from benchmarks import owned_inventory_ui_contract as contract
    value=contract.validate_admission(admission)
    contract.revalidate_inputs(value)
    result=verify_frozen_product(value['artifacts'])
    contract.revalidate_inputs(value)
    return result
