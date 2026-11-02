"""Fixed B80 byte attestation; construction/import never publishes or runs tools.

Recorded XML/DEX/ELF/signer evidence is bound by bytes, not semantically rerun.
Host fixtures, compiled UI definitions and package audits do not qualify Android.
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

SCOPE = 'library-ui-build-v1'
MODE = 'fixed-b80-byte-attestation-v1'
# Immutable authority identity belongs to the intended SDK15 source, not this reader's location.
BASELINE_PATH = Path('D:/Worktrees/locallore-record-actions-tests-v1/benchmarks/library_ui_build_baseline.json')
BASELINE_BYTES = 29083
BASELINE_SHA256 = 'c39f35c45c1c43a1ae4ffa9e5b955b1b4f3300eec8fcdf6660a34e77107fa3f5'
_FIXED = dict(
    root='D:\\Worktrees\\locallore-player-profile-ui-v1',
    capture='D:\\Dev\\Experiments\\LocalLore\\2026-11-01-library-action-scope-v1',
    recovery='D:\\Dev\\Recovery\\LocalLore\\2026-11-01-library-action-scope-v1',
    manifest='D:/Dev/Experiments/LocalLore/2026-11-02-library-ui-harness-v1/library-ui-build-v1.json',
    head='7ab4918fa1044d960edcb1172fe7684474eb3a89',
    tested_head='8516871469f769c9363fc9189200c88a8e3a6931',
    first_count=2595, tested_count=2596, source_count=2597,
    native_capture='D:\\Dev\\Experiments\\LocalLore\\2026-11-01-creation-dismiss-scope-v1',
    native_compiled_head='7e69107ed48239393a880bb318211c15d6422a8a', native_source_count=2589,
    preservation_pairs=225, inherited_count=151, reused_count=81, new_inherited_count=70,
    inherited_bytes=54318045, new_inherited_bytes=342537,
    certificate='17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564',
    apks=dict(product_apk=dict(path='D:\\Worktrees\\locallore-player-profile-ui-v1\\apps\\android\\app\\build\\outputs\\apk\\debug\\app-debug.apk',bytes=28365001,sha256='3c355ec7568e8a6468790c417d986d413f5414f43cde2719f77a9041ea15abb6'),
              test_apk=dict(path='D:\\Worktrees\\locallore-player-profile-ui-v1\\apps\\android\\app\\build\\outputs\\apk\\androidTest\\debug\\app-debug-androidTest.apk',bytes=2541802,sha256='5a96cfd007e42a5eb7e739375316c2ba43263490c2cca784b35d91b83712b698')))
ROSTER = [
 ['library_recovery_equal','org.locallore.app.ui.LibraryActionScopeScreenTest','oldRecoverCannotBorrowAnEqualFailedRetryAndFreshUnselectedRecoveryWorks'],
 ['library_story_popup','org.locallore.app.ui.LibraryActionScopeScreenTest','oldStoryRowsAndOpenerCannotActOnReopenedOrEqualRefreshedLibrary'],
 ['library_timeline_popup','org.locallore.app.ui.LibraryActionScopeScreenTest','oldTimelineRowCannotActOnReopenedMenuAndFreshChoiceWorks'],
 ['library_screen_remount','org.locallore.app.ui.LibraryActionScopeScreenTest','disposedScreenRowCannotBorrowSameViewModelAfterRemount'],
]
DOC_DELTA = ['README.md','docs/android/LIBRARY_ACTION_SCOPE_2026-11-02.md']
ORACLE = 'apps/android/app/src/test/java/org/locallore/app/LibraryActionScopeShellTest.kt'
ORACLE_SHA256 = '98d5ddd36a109531df44f8faad745867ab949d2cc0a9fa42f9a4ab6d07ad31fb'
UI_SOURCE = 'apps/android/app/src/androidTest/java/org/locallore/app/ui/LibraryActionScopeScreenTest.kt'
SOURCE_ENCODING = 'Exact recorded raw worktree bytes; Git identity never authorizes newline normalization'
_PHASES = (
 ('first-v1','e3322589328ca64fde3bda417eab3b743fb730c5',12,11,1,13935),
 ('green-v1','1e308da3fc56357f69c93c71dc2045e7e2412b29',12,0,0,23748),
 ('green-v2','10daaf039da6ce46a8d608ca3f3259579abad528',12,0,0,15408),
 ('android-v1','10daaf039da6ce46a8d608ca3f3259579abad528',550,0,1,41875),
 ('green-v3','8516871469f769c9363fc9189200c88a8e3a6931',12,0,0,8791),
 ('android-v2','8516871469f769c9363fc9189200c88a8e3a6931',550,0,0,43352),
)
_FACTS = dict(android_runtime_executed=False,model_material=False,deep_semantic_review_repeated=False,
 full_tool_binary_provenance=False,full_cache_or_TEMP_meter=False,jvm_cases=550,jvm_suites=67,
 jvm_failures=0,jvm_errors=0,jvm_skips=0,selected_runtime_methods=4,compiled_ui_methods=4,
 intermediate_cohorts_additive=False,failed_whole_gate_passed=False,failed_old_test_apk_qualified=False,
 fresh_native_compilation=False)

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
    out=Path(_FIXED['capture']);native=Path(_FIXED['native_capture'])
    values={name:out/filename for name,filename in (
        ('closed','closed-evidence-v1.json'),('review','closed-review-v1.json'),
        ('source_review','source-review-v2.json'),('source_review_prior','source-review-v1.json'),
        ('preservation','final-preservation-v1.json'),('preservation_review','final-preservation-review-v1.json'),
        ('final_source','final-source-map-v1.json'),('inherited','inherited-build-preservation-v1.json'),
        ('helper','run-check-v1.py'))}
    for name,head,*_ in _PHASES:
        for role,file in (('before','source-before-v1.json'),('after','source-after-v1.json'),
            ('request','request-v1.json'),('actual_child','actual-child-v1.json'),
            ('command_child','command-child-v1.json'),('command_terminal','command-terminal-v1.json'),
            ('owner','owner-result-v1.json'),('terminal','terminal-v1.json'),
            ('stdout','owner-stdout-v1.bin'),('stderr','owner-stderr-v1.bin'),
            ('reports','partial-preservation-v1.json' if name=='android-v1' else 'report-preservation-v1.json')):
            values[name+'/'+role]=out/name/file
        values['zip/'+head]=out/('source-'+head+'.zip')
    for role,file in (('before','source-before-v1.json'),('after','source-after-v1.json'),
        ('owner','owner-result-v1.json'),('terminal','terminal-v1.json'),('request','request-v1.json'),
        ('stdout','owner-stdout-v1.bin'),('stderr','owner-stderr-v1.bin')):
        values['native/'+role]=native/'first-v1'/file
    values['native/zip']=native/('source-'+_FIXED['native_compiled_head']+'.zip')
    return values


def _binary(key):
    return key=='helper' or key.startswith('zip/') or key.endswith(('/stdout','/stderr','/zip'))


def _baseline(reader):
    identity=dict(path=str(BASELINE_PATH),bytes=BASELINE_BYTES,sha256=BASELINE_SHA256)
    value=reader.json(identity)
    _keys(value,('version','scope','product','refs','roster','facts','native','documentation_only_delta','source_encoding'))
    _need(type(value['version']) is int and value['version']==1 and value['scope']==MODE and
        _same(value['product'],_FIXED) and _same(value['roster'],ROSTER) and _same(value['facts'],_FACTS) and
        value['documentation_only_delta']==DOC_DELTA and value['source_encoding']==SOURCE_ENCODING,'baseline')
    paths=_paths();_keys(value['refs'],paths)
    for key,path in paths.items():
        _binding(value['refs'][key]);_need(Path(value['refs'][key]['path'])==path,'baseline_path')
    return value,identity


def _integer(value,expected):
    _need(type(value) is int and value==expected,'count')


def _identity(value):
    _keys(value,('pid','creation_filetime','executable'))
    _need(type(value['pid']) is int and value['pid']>0 and type(value['creation_filetime']) is int and
        value['creation_filetime']>0 and type(value['executable']) is str and
        Path(value['executable']).is_absolute(),'identity')


def _pair(reader,value,*,current=False):
    _keys(value,('source','copy'))
    for pin in value.values():_binding(pin)
    _need(_same({k:value['source'][k] for k in ('bytes','sha256')},
                {k:value['copy'][k] for k in ('bytes','sha256')}),'copy')
    reader.read(value['copy'])
    if current:reader.read(value['source'])


def _source(reader,base,r):
    _need(_git(['rev-parse','HEAD']).decode('ascii').strip()==_FIXED['head'] and
          _git(['status','--porcelain','--untracked-files=all'])==b'','source')
    maps={}
    for name,head,*_ in _PHASES:
        before,after=r[name+'/before'],r[name+'/after']
        _need(_same(before,after) and before['head']==head,'source')
        maps[name]=_rows(before['files'],_FIXED['first_count'] if name=='first-v1' else _FIXED['tested_count'])
        _need(maps[name][ORACLE]['sha256']==ORACLE_SHA256,'oracle')
        _need(_same(r[name+'/request']['source_archive'],base['refs']['zip/'+head]),'source_archive')
    _need(_same(maps['green-v2'],maps['android-v1']) and _same(maps['green-v3'],maps['android-v2']),'source')
    _need(set(maps['green-v2'])==set(maps['green-v3']) and
          all(_same(row,maps['green-v3'][name]) for name,row in maps['green-v2'].items() if name!=UI_SOURCE),'test_only_fix')
    final=r['final_source'];_need(final['head']==_FIXED['head'],'source')
    current=_rows(final['files'],_FIXED['source_count']);tested=maps['green-v3']
    _need(sorted(k for k in current.keys()|tested.keys() if current.get(k)!=tested.get(k))==DOC_DELTA and
          set(current)-set(tested)=={DOC_DELTA[1]} and not set(tested)-set(current),'source_overlay')
    names=_git(['ls-files','-z']).decode('utf-8').split('\0')
    _need(names[-1]=='' and len(names[:-1])==len(set(names[:-1]))==len(current) and set(names[:-1])==set(current),'source_roster')
    for pin in current.values():reader.read(pin)
    for key in ('source_review_prior','source_review'):
        _need(r[key]['result']=='no-concrete-source-blocker-found','source_review')
    _need(_same(r['source_review']['previous_review'],base['refs']['source_review_prior']),'source_review')
    for row in r['source_review']['production_comparison']:
        _need(row['matches_prior'] is True,'source_review');reader.read({k:row[k] for k in ('path','bytes','sha256')})
    return current,maps


def _execution(reader,base,r):
    names=None
    for phase,head,tests,failures,code,elapsed in _PHASES:
        owner,terminal,request=(r[phase+'/'+role] for role in ('owner','terminal','request'))
        _need(_same(terminal['owner'],owner) and owner['status']=='child_exited' and
            owner['cleanup_complete'] is True and owner['output_capture_complete'] is True and
            terminal['source_equal'] is True and terminal['faults']==[] and
            terminal['passed'] is (code==0),'owner')
        _integer(owner['worker_returncode'],code);_integer(owner['elapsed_ms'],elapsed)
        _integer(r[phase+'/command_terminal']['returncode'],code)
        _need(request['head']==head and Path(request['cwd'])==Path(_FIXED['root']),'request')
        _integer(request['seconds'],900)
        _need(_same(request['helper'],{k:base['refs']['helper'][k] for k in ('bytes','sha256')}),'helper')
        actual,child=r[phase+'/actual_child'],r[phase+'/command_child']
        _need(_same(actual['helper'],request['helper']),'helper')
        for value in (request['owner'],actual['identity'],child['identity']):_identity(value)
        _need(len({request['owner']['pid'],actual['identity']['pid'],child['identity']['pid']})==3 and
            request['owner']['creation_filetime']<=actual['identity']['creation_filetime']<=child['identity']['creation_filetime'] and
            request['owner']['executable']==actual['identity']['executable'],'identity')
        full=phase.startswith('android-')
        command=([request['owner']['executable'],'-I','-S','-B','scripts/check.py','android','--offline'] if full else
            [str(Path(_FIXED['root'])/'apps/android/gradlew.bat'),'-p','apps/android','--offline','--no-daemon','--max-workers=2',
             ':app:testDebugUnitTest','--tests','org.locallore.app.LibraryActionScopeShellTest'])
        _need(request['command']==child['command']==command,'command')
        _need((child['identity']['executable']==actual['identity']['executable']) if full else
              Path(child['identity']['executable']).name.lower()=='cmd.exe','identity')
        for channel in ('stdout','stderr'):
            _integer(owner[channel+'_bytes'],base['refs'][phase+'/'+channel]['bytes'])
        raw=reader.read(base['refs'][phase+'/stdout'],data=True).decode('utf-8')
        _need('> Task :app:buildRustAndroid UP-TO-DATE' in raw and 'Building LocalLore Rust JNI:' not in raw,'native_attribution')
        reports=r[phase+'/reports'];partial=phase=='android-v1'
        rows=reports['jvm_xml'] if partial else reports['files']
        if phase=='android-v2':_integer(len(rows),72)
        seen=set();xml=0
        for pair in rows:
            original,copy_path=Path(pair['source']['path']),Path(pair['copy']['path'])
            _need(original not in seen,'reports');seen.add(original)
            if original.suffix=='.xml' and original.name.startswith('TEST-'):
                xml+=1
                _need(original.parent==Path(_FIXED['root'])/'apps/android/app/build/test-results/testDebugUnitTest' and
                    copy_path==Path(_FIXED['capture'])/phase/('partial-reports-v1' if partial else 'reports')/original.name,'reports')
            _pair(reader,pair,current=phase=='android-v2')
        _integer(xml,67 if full else 1);_integer(reports['tests'],tests)
        _integer(reports['failures'],failures);_integer(reports['errors'],0);_integer(reports['skipped'],0)
        if partial:
            _need(reports['overall_passed'] is False and _same(reports['phase_terminal'],base['refs'][phase+'/terminal']),'failed_gate')
            _need(':app:compileDebugAndroidTestKotlin FAILED' in raw and 'audit_apk.py' not in raw and
                'audit_instrumentation_apk.py' not in raw,'failed_gate')
            errors=reader.read(base['refs'][phase+'/stderr'],data=True).decode('utf-8')
            _need("Unresolved reference 'Espresso'" in errors and "Unresolved reference 'pressBack'" in errors,'failed_gate')
            _pair(reader,reports['failed_current_product']);_pair(reader,reports['inherited_test_apk'])
            _need(Path(reports['failed_current_product']['copy']['path'])==Path(_FIXED['recovery'])/'failed-build-v1/app-debug.apk' and
                reports['inherited_test_apk']['copy']['sha256']!=_FIXED['apks']['test_apk']['sha256'],'failed_attribution')
        else:
            cases=reports['cases'];_need(type(cases) is list and len(cases)==tests,'cases')
            _integer(reports['unique'],tests)
            _need(len({(c['suite'],c['name']) for c in cases})==tests and
                sum(bool(c['failure']) for c in cases)==failures and
                all(type(c['errors']) is int and c['errors']==0 and type(c['skipped']) is int and c['skipped']==0 and
                    all(kind=='java.lang.AssertionError' for kind in c['failure']) for c in cases),'cases')
            scoped={c['name'] for c in cases if c['suite']=='org.locallore.app.LibraryActionScopeShellTest'}
            _need(len(scoped)==12 and (names is None or names==scoped),'oracle');names=scoped
    closed=r['closed'];review=r['review']
    _need(closed['lint_severities']=={'Hint':1,'Warning':1},'lint')
    _need(closed['ui_executed'] is False and closed['failed_full_gate']['overall_passed'] is False and
        closed['failed_full_gate']['old_test_apk_unqualified'] is True and closed['failed_full_gate']['final_product_audits_not_run'] is True and
        review['result']=='verified-no-evidence-mismatch' and review['findings']==[] and review['ui_execution'] is False and
        review['failed_full_gate_preserved'] is True and review['source_archives_replayed']==4,'review')
    recorded=closed['compiled_only_ui_methods'];_need(type(recorded) is list and len(recorded)==4,'methods')
    _need({p['method'] for p in recorded}=={p[2] for p in ROSTER} and
        all(p['runtime_junit'] is True and type(p['code_units']) is int and 0<p['code_units']<=8192 for p in recorded) and
        review['all_four_wrappers_delegate_to_helper'] is True and type(review['compiled_journey_code_units']) is int and review['compiled_journey_code_units']>5,'methods')


def _retention(reader,base,r):
    receipt=r['preservation'];_need(receipt['head']==_FIXED['head'] and receipt['tested_head']==_FIXED['tested_head'] and
        receipt['sources']==_FIXED['source_count'] and receipt['overlay_paths']==DOC_DELTA and
        receipt['no_full_generated_tree_backup'] is True,'retention')
    pairs=receipt['files'];_need(type(pairs) is list and len(pairs)==_FIXED['preservation_pairs'],'retention')
    originals=set();copies=set()
    for pair in pairs:
        source,preserved=Path(pair['source']['path']),Path(pair['copy']['path'])
        _need(source not in originals and preserved not in copies,'retention');originals.add(source);copies.add(preserved)
        if source.is_relative_to(Path(_FIXED['capture'])):
            expected=Path(_FIXED['recovery'])/'controls-v1'/source.relative_to(Path(_FIXED['capture']))
        else:
            _need(source.is_relative_to(Path(_FIXED['root'])) and source.relative_to(Path(_FIXED['root'])).as_posix() in DOC_DELTA,'retention')
            expected=Path(_FIXED['recovery'])/'final-source-overlay-v1'/source.relative_to(Path(_FIXED['root']))
        _need(preserved==expected,'retention_path');_pair(reader,pair,current=True)
    canonical=Path(_FIXED['recovery'])/'final-preservation-v1.json'
    reader.read(dict(base['refs']['preservation'],path=str(canonical)))
    review=r['preservation_review'];_need(review['result']=='verified-no-mismatch' and review['findings']==[] and
        review['head']==_FIXED['head'] and review['reconstructed_source_files']==_FIXED['source_count'] and
        _same(review['manifest'],base['refs']['preservation']),'retention_review')
    inherited=r['inherited'];_integer(len(inherited['files']),_FIXED['inherited_count'])
    _integer(inherited['total_bytes'],_FIXED['inherited_bytes']);_integer(inherited['new_copy_bytes'],_FIXED['new_inherited_bytes'])
    reused=0;new_bytes=0;total=0;seen=set()
    for pair in inherited['files']:
        _pair(reader,{k:pair[k] for k in ('source','copy')})
        path=Path(pair['copy']['path']);_need(path not in seen,'inherited');seen.add(path);total+=pair['copy']['bytes']
        if pair.get('reused_immutable_copy') is True:reused+=1
        else:
            _need(path.is_relative_to(Path(_FIXED['recovery'])) and path.suffix not in ('.apk','.so'),'inherited')
            new_bytes+=pair['copy']['bytes']
    _integer(reused,_FIXED['reused_count']);_integer(len(seen)-reused,_FIXED['new_inherited_count'])
    _integer(new_bytes,_FIXED['new_inherited_bytes']);_integer(total,_FIXED['inherited_bytes'])


def _native(reader,base,r,current):
    old=r['native/before'];_need(_same(old,r['native/after']) and old['head']==_FIXED['native_compiled_head'],'native_source')
    rows=_rows(old['files'],_FIXED['native_source_count'])
    crates={k:v for k,v in current.items() if k.startswith('crates/')}
    _need(crates and all(k in rows and _same(v,rows[k]) for k,v in crates.items()),'native_source')
    owner=r['native/owner'];terminal=r['native/terminal']
    _need(_same(terminal['owner'],owner) and owner['status']=='child_exited' and owner['worker_returncode']==1 and
        owner['cleanup_complete'] is True and owner['output_capture_complete'] is True and terminal['source_equal'] is True and
        terminal['passed'] is False and terminal['faults']==[],'native_owner')
    text=reader.read(base['refs']['native/stdout'],data=True).decode('utf-8')
    _need(all(token in text for token in ('Building LocalLore Rust JNI: x86_64-linux-android','Building LocalLore Rust JNI: aarch64-linux-android')),'native_origin')
    values=base['native'];_need(type(values) is list and len(values)==2,'native')
    root=Path(_FIXED['root'])/'apps/android/app/build'
    for row,(target,abi) in zip(values,(('x86_64-linux-android','x86_64'),('aarch64-linux-android','arm64-v8a'))):
        paths=dict(release=root/f'rust-target/{target}/release/liblocallore_android.so',cargo_alias=root/f'rust-target/{target}/release/deps/liblocallore_android.so',
            generated=root/f'generated/rustJniLibs/{abi}/liblocallore_android.so',merged=root/f'intermediates/merged_native_libs/debug/mergeDebugNativeLibs/out/lib/{abi}/liblocallore_android.so',
            stripped=root/f'intermediates/stripped_native_libs/debug/stripDebugDebugSymbols/out/lib/{abi}/liblocallore_android.so')
        _need(row['abi']==abi and all(Path(row[k]['path'])==p for k,p in paths.items()),'native_path')
        reader.native_pair(row['release'],row['cargo_alias'])
        for key in ('generated','merged','stripped'):reader.read(row[key])
        _need(len({row[k]['sha256'] for k in ('release','cargo_alias','generated','merged')})==1 and
            row['release_alias_links']==2 and row['apk_sha256']==row['stripped']['sha256'],'native_bytes')


def _create_manifest():
    reader=_Reader();base,identity=_baseline(reader)
    r={key:reader.json(pin) for key,pin in base['refs'].items() if not _binary(key)}
    for key,pin in base['refs'].items():
        if _binary(key):reader.read(pin)
    current,maps=_source(reader,base,r);_execution(reader,base,r);_retention(reader,base,r);_native(reader,base,r,current)
    output=reader.read(base['refs']['android-v2/stdout'],data=True).decode('utf-8')
    _need('81 actionable tasks: 8 executed, 73 up-to-date' in output and 'BUILD SUCCESSFUL' in output,'audit')
    first=json.JSONDecoder().raw_decode(output[output.index('{'):])[0]
    pair=_json(output.splitlines()[-1].encode('utf-8'))
    _need(first['status']==pair['status']=='passed' and first['permissions']==[] and len(first['libraries'])==4 and
        pair['package']=='org.locallore.app' and pair['test_package']=='org.locallore.app.test' and
        pair['certificate_sha256']==_FIXED['certificate'] and pair['test_permissions']==['android.permission.REORDER_TASKS'],'audit')
    apks={};reports=r['android-v2/reports']
    for role,pin in _FIXED['apks'].items():
        key='app' if role=='product_apk' else 'test'
        row=next(value for value in reports['files'] if value['source']==pin)
        _need(Path(row['copy']['path'])==Path(_FIXED['recovery'])/'current-build-v1'/('outputs__apk__debug__app-debug.apk' if key=='app' else 'outputs__apk__androidTest__debug__app-debug-androidTest.apk'),'apk_copy')
        _pair(reader,row,current=True);_need(_same(pair[key],{k:pin[k] for k in ('bytes','sha256')}),'apk')
        apks[role]=dict(binding=copy.deepcopy(pin),package='org.locallore.app'+('.test' if key=='test' else ''),certificate_sha256=_FIXED['certificate'])
    _need(_git(['rev-parse','HEAD']).decode('ascii').strip()==_FIXED['head'] and _git(['status','--porcelain','--untracked-files=all'])==b'','source')
    reader.final()
    return dict(version=1,scope=SCOPE,validation_mode=MODE,baseline=identity,roster=copy.deepcopy(ROSTER),apks=apks,
        product_source={k:copy.deepcopy(_FIXED[k]) for k in ('root','head','tested_head','source_count','tested_count')},
        recorded_execution=dict(facts=copy.deepcopy(_FACTS),bindings=copy.deepcopy(base['refs']),phases=[list(p) for p in _PHASES],documentation_only_delta=DOC_DELTA[:],source_encoding=SOURCE_ENCODING),
        current_native_bindings=copy.deepcopy(base['native']))


def create_manifest():
    """Return validated data only. No import/constructor/reader publishes a file."""
    try:return _create_manifest()
    except BuildRefused:raise
    except (OSError,ValueError,KeyError,TypeError,IndexError,StopIteration,RecursionError,UnicodeError,subprocess.SubprocessError):
        raise BuildRefused('build') from None


def verify_frozen_product(artifacts):
    try:
        _keys(artifacts,('build','product_apk','test_apk'))
        for pin in artifacts.values():_binding(pin)
        _need(Path(artifacts['build']['path'])==Path(_FIXED['manifest']) and artifacts['build']['bytes']<=2*1024**2 and
            all(_same(artifacts[role],pin) for role,pin in _FIXED['apks'].items()),'artifacts')
        reader=_Reader();actual=reader.json(artifacts['build']);expected=create_manifest()
        _need(_same(actual,expected),'manifest')
        for role in _FIXED['apks']:reader.read(artifacts[role])
        reader.final();return copy.deepcopy(expected)
    except BuildRefused:raise
    except (OSError,ValueError,KeyError,TypeError,IndexError,RecursionError):raise BuildRefused('build') from None


def verify_current(admission):
    from benchmarks import owned_library_ui_contract as contract
    value=contract.validate_admission(admission);contract.revalidate_inputs(value)
    result=verify_frozen_product(value['artifacts']);contract.revalidate_inputs(value);return result



