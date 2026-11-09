"""Fixed B48 ordinary APK evidence replay; no import I/O or target operations.

The recorded Gradle phases and audits are not a supervised public-check capture.
Current source revalidation does not invent a historical raw-source/child graph.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import ast
from collections import Counter
import copy
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import time
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).parents[1]
PRODUCT_ROOT = Path("D:/Dev/Projects/The Hero's Journey/LocalLore-storage-review")
PRODUCT_HEAD = '78f254bb50ca0478541f0107ccfbcb16afd40d72'
CAPTURE = Path('D:/Dev/Experiments/LocalLore/2026-11-01-transcript-rollover-v1')
RECOVERY = Path('D:/Dev/Recovery/LocalLore/2026-11-01-transcript-rollover-v1')
MANIFEST_PATH = Path('D:/Dev/Experiments/LocalLore/2026-11-01-transcript-ui-cohort-v1/transcript-ui-build-v1.json')
SCOPE = 'transcript-ui-build-v1'
APP = 'org.locallore.app'
CERTIFICATE = '17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564'
APK_BINDINGS = {
    'product_apk': dict(path=str(PRODUCT_ROOT / 'apps/android/app/build/outputs/apk/debug/app-debug.apk'),
        bytes=28012664, sha256='16b3b7761d64991c5906cb67c24ad8e562006acc1a349201a3b883fd7145d6d9'),
    'test_apk': dict(path=str(PRODUCT_ROOT / 'apps/android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk'),
        bytes=2275810, sha256='1b598a0f05ac1f24a85fef035d7c16a9ed5fabfb4cee988c7b5a9a028b68ee8e'),
}
SELECTORS = (
    ('transcript_history', 'org.locallore.app.TranscriptFollowScreenTest', 'readingHistoryKeepsPositionUntilLatestAndPreservesTheUnsentDialogue'),
    ('transcript_tail', 'org.locallore.app.TranscriptFollowScreenTest', 'seeingOnlyTheHeadOfALongTailDoesNotAuthorizeFollowingAnAppend'),
    ('transcript_composer', 'org.locallore.app.TranscriptFollowScreenTest', 'readingTheComposerPastTheTailFollowsTheNewReplyWithoutSubmittingTheDraft'),
    ('transcript_branch', 'org.locallore.app.TranscriptFollowScreenTest', 'retainedLatestCallbackCannotNavigateAnotherBranchWithReusedMessageIds'),
    ('transcript_rollover_follow', 'org.locallore.app.ui.TranscriptRolloverUiTest', 'readerBelowFortyRowTailSeesRolledReplyWithoutScrollingOrSendingDraft'),
    ('transcript_rollover_history', 'org.locallore.app.ui.TranscriptRolloverUiTest', 'historyReaderKeepsSurvivingRowUntilLatestAndKeepsOriginalDraft'),
)
CRITICAL_SOURCES = {
    'apps/android/app/src/main/java/org/locallore/app/TranscriptFollow.kt': 'a5584a4f89bba1708f26ccb1d3d1327072dcd726eb1322faf93361f32d7a1b61',
    'apps/android/app/src/test/java/org/locallore/app/TranscriptRolloverTest.kt': '494ba75116d64980e73821c0e248a068615cf63d19e064f35d5ecc7bdae2ad0b',
    'apps/android/app/src/androidTest/java/org/locallore/app/ui/TranscriptRolloverUiTest.kt': 'e0e4ce794678c6d8786af1ac301b980d360f7114213637721f96d1b63ea47af0',
    'apps/android/app/src/androidTest/java/org/locallore/app/TranscriptFollowScreenTest.kt': '2de207f4c0d2ec804b417fda7ea1edffd76a530b2bd487d62d8b4eb392041885',
}
CAPTURE_SEALS = {
    'execution-v1.json': (2487, 'cd8c3c258840206fa5a4f6966d1d2f32ef4b56a28454db8cdd056611b2fb107b'),
    'host-report-copies-v1.json': (22960, '6416b977ea401685d8a76b866780dce283e2c4bd92f8d46da69e5f90c1addffa'),
    'full-android-host-v1.log': (3013, 'a501d0b6ac99beded1793403cdd4b24e877bec65881a592a3b0aadcc57d51f21'),
    'apk-build-v1.log': (7816, 'f46dfa3f024a00f2de6d7eb2e4a9435a0bcd12fac849ad5c979ed1753bdf61d4'),
    'pair-audit-v1.json': (456, '6329975a30a59e1b5b3af30a5ef66b2fb4827bba7db66f7fb98bade2e6582617'),
    'product-audit-v1.json': (783, 'a2220741ab7d3170dc6f144e8b0c0d97b3b85457ef46d7bf0d6e0c76a8cef49f'),
    'first-jvm-v1.log': (2826, '1ab7bc215fbe6c7e18a2ade49cbb8ef09f532970b2fcad5562c330153711a42c'),
    'focused-green-v1.log': (1451, 'e824effafe235556ecaed9003c91f54f1bf8a1f9b0dc96718ec5f18d70ff30b5'),
    'FIRST-TranscriptRolloverTest-v1.xml': (25675, '4a6d39d087fa06644c8af37ad1f437a75d330d39b2526abf07ec31b2fcbfc8b9'),
    'GREEN-TranscriptRolloverTest-v1.xml': (1669, '294f6590e178bcdc8275f588db64679dbfe6e6934591f9afb77a1b2938664a62'),
    'GREEN-TranscriptFollowTest-v1.xml': (1551, 'b5cb69674b79a79acfcaa8d749b865c4832d91bc1d625fa72f00450d3f8bc120'),
}
PRESERVATION = dict(path=str(RECOVERY / 'preservation-manifest-v1.json'), bytes=27588,
    sha256='e7c88be0b972b8d5924119fa7ae12bd1b8b7ea9b5791c4923c3d606ed1400161')
ARCHIVE = dict(path=str(RECOVERY / 'source-78f254bb.zip'), bytes=11347161,
    sha256='bcdd030d78f601b4ea5b39c4efa40ae8ee47aeb6e77d0b0403787ac90363fc31')


class BuildRefused(ValueError):
    """Bounded public reason; never private payload or signing material."""


def _need(value, reason='build'):
    if not value:
        raise BuildRefused(reason)


def _keys(value, fields):
    _need(type(value) is dict and set(value) == set(fields), 'shape')


def _same(left, right):
    # JSON equality distinguishes booleans from numbers, unlike Python dict equality.
    return json.dumps(left, sort_keys=True, allow_nan=False) == json.dumps(right, sort_keys=True, allow_nan=False)


def _relative(name):
    _need(type(name) is str and name and '\\' not in name, 'path')
    path = PurePosixPath(name)
    _need(not path.is_absolute() and not re.match('[A-Za-z]:', name) and
          all(part not in ('', '.', '..') for part in name.split('/')), 'path')
    return path


def _ordinary(path):
    path = Path(path)
    _need(path.is_absolute() and path.drive.upper() == 'D:' and path.resolve(strict=True) == path, 'path')
    for part in (path, *path.parents):
        info = part.lstat()
        _need(not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 1024 and
              (part == path or stat.S_ISDIR(info.st_mode)), 'path')
    info = path.lstat()
    _need(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, 'file')
    return info


def _stamp(info):
    return tuple(getattr(info, key) for key in ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns', 'st_nlink', 'st_mode'))


class _Reader:
    def __init__(self):
        self.deadline = time.monotonic() + 120
        self.checked = {}

    def raw(self, path, cap=64*1024**2):
        _need(time.monotonic() < self.deadline, 'deadline')
        path = Path(path)
        before = _ordinary(path)
        _need(0 <= before.st_size <= cap, 'size')
        with path.open('rb') as stream:
            held = os.fstat(stream.fileno())
            common = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_nlink, stat.S_IFMT(s.st_mode))
            _need(common(before) == common(held), 'identity')
            raw = bytearray()
            while len(raw) <= before.st_size:
                _need(time.monotonic() < self.deadline, 'deadline')
                block = stream.read(min(1024**2, before.st_size-len(raw)+1))
                if not block:
                    break
                raw.extend(block)
            _need(_stamp(held) == _stamp(os.fstat(stream.fileno())), 'changed')
        _need(len(raw) == before.st_size and _stamp(before) == _stamp(_ordinary(path)), 'changed')
        pin = dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        if path in self.checked:
            _need(_same(pin, self.checked[path][0]) and _stamp(before) == self.checked[path][1], 'changed')
        self.checked[path] = (pin, _stamp(before))
        return bytes(raw)

    def pin(self, path):
        self.raw(path)
        return copy.deepcopy(self.checked[Path(path)][0])

    def bound(self, value, cap=64*1024**2):
        _binding(value)
        raw = self.raw(value['path'], cap)
        _need(_same(value, self.checked[Path(value['path'])][0]), 'binding')
        return raw

    def final(self):
        for path in list(self.checked):
            self.raw(path)


def _binding(value):
    _keys(value, ('path', 'bytes', 'sha256'))
    _need(type(value['path']) is str and type(value['bytes']) is int and 0 <= value['bytes'] <= 64*1024**2 and
          type(value['sha256']) is str and re.fullmatch('[0-9a-f]{64}', value['sha256']), 'binding')


def _json(raw):
    def pairs(rows):
        result = {}
        for key, value in rows:
            _need(key not in result, 'json')
            result[key] = value
        return result
    return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
        parse_constant=lambda _: (_ for _ in ()).throw(BuildRefused('json')))


def _git(args):
    _need(args in (['rev-parse', 'HEAD'], ['status', '--porcelain', '--untracked-files=all'], ['ls-files', '-z']), 'git')
    _need(PRODUCT_ROOT.is_absolute() and PRODUCT_ROOT.drive.upper() == 'D:' and
          PRODUCT_ROOT.resolve(strict=True) == PRODUCT_ROOT, 'path')
    for parent in (PRODUCT_ROOT, *PRODUCT_ROOT.parents):
        info = parent.lstat()
        _need(stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode) and
              not getattr(info, 'st_file_attributes', 0) & 1024, 'path')
    answer = subprocess.run(['git', '--no-optional-locks', '-C', str(PRODUCT_ROOT)] + args,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15,
        env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'))
    _need(answer.returncode == 0 and answer.stderr == b'', 'source')
    return answer.stdout


def _source(reader):
    _need(_git(['rev-parse', 'HEAD']).decode('ascii').strip() == PRODUCT_HEAD and
          _git(['status', '--porcelain', '--untracked-files=all']) == b'', 'source')
    names = _git(['ls-files', '-z']).decode('utf-8').split('\0')
    _need(names[-1] == '' and len(names[:-1]) == len(set(names[:-1])) and names[:-1], 'source')
    result = {}
    for name in names[:-1]:
        _relative(name)
        result[name] = hashlib.sha256(reader.raw(PRODUCT_ROOT / name, 8*1024**2)).hexdigest()
    return result


def _archive(reader, sources):
    with zipfile.ZipFile(io.BytesIO(reader.bound(ARCHIVE))) as archive:
        rows = archive.infolist()
        _need(len(rows) <= 4096 and len({r.filename for r in rows}) == len(rows) and
              sum(r.file_size for r in rows) <= 64*1024**2 and archive.comment.decode('ascii') == PRODUCT_HEAD, 'archive')
        files = {}
        for row in rows:
            _relative(row.filename.rstrip('/'))
            kind = stat.S_IFMT(row.external_attr >> 16)
            _need(not row.flag_bits & 1 and kind in (0, stat.S_IFDIR, stat.S_IFREG), 'archive')
            if not row.is_dir():
                _need(row.file_size <= 8*1024**2, 'archive')
                files[row.filename] = archive.read(row)  # Also checks each member CRC.
        _need(set(files) == set(sources), 'source')
        for name, digest in CRITICAL_SOURCES.items():
            _need(sources[name] == digest and hashlib.sha256(files[name]).hexdigest() == digest, 'source')
    return dict(binding=copy.deepcopy(ARCHIVE), files=len(files), format='canonical-git-archive')


def _xml(raw):
    _need(len(raw) <= 2*1024**2 and b'<!DOCTYPE' not in raw.upper() and b'<!ENTITY' not in raw.upper(), 'xml')
    return ET.fromstring(raw)


def _cases(raw, tests=None, failures=0):
    suite = _xml(raw)
    rows = suite.findall('testcase')
    _need(suite.tag == 'testsuite' and list(suite.iter('testsuite')) == [suite] and
          list(suite.iter('testcase')) == rows and int(suite.attrib['tests']) == len(rows) and
          (tests is None or len(rows) == tests), 'jvm')
    _need(int(suite.attrib['failures']) == failures and int(suite.attrib['errors']) == 0 and
          int(suite.attrib['skipped']) == 0 and len(list(suite.iter('failure'))) == failures and
          not list(suite.iter('error')) and not list(suite.iter('skipped')), 'jvm')
    _need(all(case.get('classname') == suite.get('name') and case.get('name') for case in rows), 'jvm')
    identities = [(case.get('classname'), case.get('name')) for case in rows]
    _need(len(identities) == len(set(identities)), 'jvm')
    return identities


def _tasks(raw, names, ending):
    text = raw.decode('utf-8')
    for name in names:
        expected = '> Task :app:' + name
        rows = [line for line in text.splitlines() if line == expected or line.startswith(expected+' ')]
        _need(rows and all(row == expected for row in rows), 'freshness')
    _need(ending in text, 'phase')


def _phases(records):
    _tasks(records['full-android-host-v1.log'], ('testDebugUnitTest', 'compileDebugAndroidTestKotlin',
        'lintAnalyzeDebug', 'lintReportDebug', 'lintDebug'), 'BUILD SUCCESSFUL in 53s')
    _tasks(records['focused-green-v1.log'], ('compileDebugKotlin', 'testDebugUnitTest'), 'BUILD SUCCESSFUL in 33s')
    _tasks(records['apk-build-v1.log'], ('buildRustAndroid', 'packageDebug', 'assembleDebug',
        'packageDebugAndroidTest', 'assembleDebugAndroidTest'), 'BUILD SUCCESSFUL in 2m 50s')
    _need(b'BUILD FAILED in 47s' in records['first-jvm-v1.log'] and
          b'9 tests completed, 6 failed' in records['first-jvm-v1.log'], 'first')


def _helpers(reader):
    # Full scripts differ by an unrelated opt-in profile. Compare the reused
    # pure decoder bodies, not an invented whole-module equality requirement.
    modules = {}
    for relative, names in (('scripts/audit_physical_model_apk.py', ('Dex', 'dex_classes')),
                            ('scripts/audit_apk.py', ('require',))):
        bodies = []
        for root in (PRODUCT_ROOT, ROOT):
            raw = reader.raw(root / relative)
            tree = ast.parse(raw)
            selected = {node.name: ast.dump(node, include_attributes=False) for node in tree.body
                if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and node.name in names}
            _need(set(selected) == set(names), 'parser')
            bodies.append(selected)
        _need(bodies[0] == bodies[1], 'parser')
        modules[relative] = dict(product=reader.pin(PRODUCT_ROOT / relative), launcher=reader.pin(ROOT / relative))
    relative = 'benchmarks/android_instrumentation_evidence.py'
    _need(reader.raw(PRODUCT_ROOT / relative) == reader.raw(ROOT / relative), 'parser')
    modules[relative] = dict(product=reader.pin(PRODUCT_ROOT / relative), launcher=reader.pin(ROOT / relative))
    return modules


def _selectors(reader):
    from benchmarks import android_instrumentation_evidence as evidence
    from scripts import audit_physical_model_apk as physical
    _need(Path(evidence.__file__).resolve() == ROOT / 'benchmarks/android_instrumentation_evidence.py' and
          Path(physical.__file__).resolve() == ROOT / 'scripts/audit_physical_model_apk.py' and
          Path(physical.base.__file__).resolve() == ROOT / 'scripts/audit_apk.py', 'parser')
    app = physical.dex_classes(Path(APK_BINDINGS['product_apk']['path']))
    test = physical.dex_classes(Path(APK_BINDINGS['test_apk']['path']))
    classes = {}
    for _, klass, method in SELECTORS:
        classes.setdefault(klass, []).append(method)
    for klass, methods in classes.items():
        path = PRODUCT_ROOT / 'apps/android/app/src/androidTest/java' / (klass.replace('.', '/') + '.kt')
        reader.pin(path)
        _need(evidence.test_roster(path) == methods, 'roster')
        descriptor = ('L' + klass.replace('.', '/') + ';').encode('ascii')
        _need(descriptor not in app and descriptor in test, 'dex')
        flags, definitions = test[descriptor]
        _need(flags & 1 and not flags & (0x200 | 0x400), 'dex')
        for method in methods:
            found = [(proto, flag, junit) for name, proto, flag, junit in definitions if name == method.encode('ascii')]
            _need(len(found) == 1 and found[0][0] == (b'V', 0) and found[0][1] & 1 and
                  not found[0][1] & (8 | 0x400) and found[0][2] is True, 'dex')


def _reports(reader, rows, records):
    from benchmarks import android_instrumentation_evidence as evidence
    _need(Path(evidence.__file__).resolve() == ROOT / 'benchmarks/android_instrumentation_evidence.py', 'parser')
    _need(type(rows) is list and len(rows) == 50, 'report')
    report_root = PRODUCT_ROOT / 'apps/android/app/build/test-results/testDebugUnitTest'
    expected = sorted(report_root.glob('TEST-*.xml'))
    identities, originals, lint, compiled = [], [], None, None
    _need(len({row['source'] for row in rows}) == len({row['copy'] for row in rows}) == 50, 'report')
    for row in rows:
        _keys(row, ('source', 'copy', 'bytes', 'sha256'))
        original = dict(path=row['source'], bytes=row['bytes'], sha256=row['sha256'])
        copied = dict(path=row['copy'], bytes=row['bytes'], sha256=row['sha256'])
        source, target = Path(row['source']), Path(row['copy'])
        _need(target.parent == CAPTURE / 'host-reports-v1' and target.name == source.name, 'report')
        raw = reader.bound(original, 2*1024**2)
        _need(reader.bound(copied, 2*1024**2) == raw, 'report')
        if source.name.startswith('TEST-'):
            _need(source.parent == report_root, 'report')
            _need(source.name == 'TEST-' + str(_xml(raw).get('name')) + '.xml', 'report')
            identities.extend(_cases(raw))
            originals.append(source)
        elif source.name == 'lint-results-debug.xml':
            _need(source == PRODUCT_ROOT / 'apps/android/app/build/reports/lint-results-debug.xml', 'lint')
            tree = _xml(raw)
            issues = Counter((x.get('id'), x.get('severity')) for x in tree.findall('issue'))
            _need(tree.tag == 'issues' and issues == Counter({('GradleDependency','Warning'):1,
                ('AutoboxingStateCreation','Hint'):1}), 'lint')
            lint = original
        else:
            _need(source == PRODUCT_ROOT / 'apps/android/app/build/tmp/kotlin-classes/debugAndroidTest/org/locallore/app/ui/TranscriptRolloverUiTest.class', 'compiled')
            _need(raw.startswith(b'\xca\xfe\xba\xbe'), 'compiled')
            compiled = original
    _need(sorted(originals) == expected and len(expected) == 48 and len(identities) == len(set(identities)) == 420 and
          lint is not None and compiled is not None, 'report')
    for name, count in (('TranscriptRolloverTest', 9), ('TranscriptFollowTest', 8)):
        path = PRODUCT_ROOT / 'apps/android/app/src/test/java/org/locallore/app' / (name+'.kt')
        reader.pin(path)
        methods = evidence.test_roster(path)
        _need(len(methods) == count and {method for klass, method in identities if klass == 'org.locallore.app.'+name} == set(methods), 'jvm')
        green = _cases(records['GREEN-'+name+'-v1.xml'], count)
        _need(set(green).issubset(set(identities)), 'jvm')
    first = _cases(records['FIRST-TranscriptRolloverTest-v1.xml'], 9, 6)
    _need(set(first) == {item for item in identities if item[0] == 'org.locallore.app.TranscriptRolloverTest'}, 'first')
    return dict(suites=48, cases=420, reports=copy.deepcopy(rows), lint=lint, compiled_ui_class=compiled)


def _audits(reader, records, preservation):
    pair = _json(records['pair-audit-v1.json'])
    _keys(pair, ('status','package','test_package','test_permissions','certificate_sha256','app','test'))
    _need(pair['status'] == 'passed' and pair['package'] == APP and pair['test_package'] == APP+'.test' and
          pair['test_permissions'] == ['android.permission.REORDER_TASKS'] and pair['certificate_sha256'] == CERTIFICATE, 'package')
    apks = {}
    for role, field, package in (('product_apk','app',APP), ('test_apk','test',APP+'.test')):
        expected = APK_BINDINGS[role]
        reader.bound(expected)
        _keys(pair[field], ('bytes','sha256'))
        _need(_same(pair[field], {k:expected[k] for k in ('bytes','sha256')}), 'apk')
        rows = [row for row in preservation['copied_files'] if row['source'] == expected['path']]
        _need(len(rows) == 1 and rows[0]['bytes'] == expected['bytes'] and rows[0]['sha256'] == expected['sha256'], 'apk')
        _need(Path(rows[0]['copy']) == RECOVERY / 'apks' / ('app-debug.apk' if role=='product_apk' else 'app-debug-androidTest.apk'), 'apk')
        reader.bound(dict(path=rows[0]['copy'], bytes=expected['bytes'], sha256=expected['sha256']))
        apks[role] = dict(binding=copy.deepcopy(expected), package=package, certificate_sha256=CERTIFICATE)
    product = _json(records['product-audit-v1.json'])
    _keys(product, ('status','permissions','libraries'))
    _need(product['status'] == 'passed' and product['permissions'] == [APP+'.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION'], 'audit')
    _need(type(product['libraries']) is list and len(product['libraries']) == 4, 'audit')
    expected_names = {f'lib/{abi}/{name}' for abi in ('arm64-v8a','x86_64') for name in ('liblocallore_android.so','libandroidx.graphics.path.so')}
    names = []
    for row in product['libraries']:
        _keys(row, ('entry','elf_load_alignment'))
        _need(type(row['elf_load_alignment']) is list and row['elf_load_alignment'] and
              all(type(value) is int and value == 16384 for value in row['elf_load_alignment']), 'audit')
        names.append(row['entry'])
    _need(len(set(names)) == 4 and set(names) == expected_names, 'audit')
    return apks


def _create_manifest():
    reader = _Reader()
    sources = _source(reader)
    archive = _archive(reader, sources)
    records, record_pins = {}, {}
    for name, (size, digest) in CAPTURE_SEALS.items():
        pin = dict(path=str(CAPTURE/name), bytes=size, sha256=digest)
        records[name] = reader.bound(pin, 2*1024**2)
        record_pins[name] = pin
    preservation = _json(reader.bound(PRESERVATION, 2*1024**2))
    _keys(preservation, ('version','source_commit','originals_retained','copy_readback','copied_files','source_archive'))
    _need(type(preservation['version']) is int and preservation['version'] == 1 and
          preservation['source_commit'] == PRODUCT_HEAD and preservation['originals_retained'] is True and
          _same(preservation['source_archive'], ARCHIVE) and len(preservation['copied_files']) == 67, 'preservation')
    execution = _json(records['execution-v1.json'])
    _need(type(execution['version']) is int and execution['version'] == 1 and execution['head'] == PRODUCT_HEAD and
          _same(execution['full_jvm'], dict(host_gate_seconds=53,errors=0,suites=48,skips=0,host_gate_exit=0,tests=420,failures=0)) and
          _same(execution['instrumentation'], dict(runtime_status='UNRUN',compiled=True,executed=0,new_cases=2)), 'execution')
    _need(_same(execution['first'], dict(gradle_exit=1,errors=0,gradle_seconds=47,skips=0,tests=9,failures=6)) and
          _same(execution['focused'], dict(gradle_exit=0,errors=0,gradle_seconds=33,skips=0,tests=17,failures=0)) and
          _same(execution['apk_build'], dict(seconds=170,native_targets=['x86_64-linux-android','aarch64-linux-android'],
              exit=0,native_seconds=[74,69])), 'execution')
    _phases(records)
    reports = _reports(reader, _json(records['host-report-copies-v1.json']), records)
    apks = _audits(reader, records, preservation)
    parsers = _helpers(reader)
    _selectors(reader)
    _need(_source(reader) == sources, 'source')
    reader.final()
    return dict(version=1, scope=SCOPE,
        product_source=dict(root=str(PRODUCT_ROOT),head=PRODUCT_HEAD,current_raw_sources=sources,
            canonical_archive=archive,critical_source_hashes=copy.deepcopy(CRITICAL_SOURCES)),
        recorded_execution=dict(scope='b48-recorded-phased-build-v1',records=record_pins,
            preservation_manifest=copy.deepcopy(PRESERVATION),historical_supervised_pipeline=False,
            historical_full_raw_source_map=False,ui_runtime_executed=False),
        apks=apks,jvm=reports,roster=[list(row) for row in SELECTORS],parser_sources=parsers)


def create_manifest():
    """Revalidate the one fixed product; return data without creating a file."""
    try:
        return _create_manifest()
    except BuildRefused:
        raise
    except (OSError, ValueError, KeyError, TypeError, IndexError, StopIteration, SyntaxError,
            RecursionError, zipfile.BadZipFile, ET.ParseError, subprocess.SubprocessError):
        raise BuildRefused('build') from None


def _artifacts(artifacts):
    _keys(artifacts, ('build','product_apk','test_apk'))
    for value in artifacts.values():
        _binding(value)
    _need(Path(artifacts['build']['path']) == MANIFEST_PATH and artifacts['build']['bytes'] <= 2*1024**2 and
          all(_same(artifacts[role], pin) for role,pin in APK_BINDINGS.items()), 'artifacts')


def verify_frozen_product(artifacts):
    """Artifact-only validation; no target/admission/profile is manufactured."""
    try:
        _artifacts(artifacts)
        reader = _Reader()
        actual = _json(reader.bound(artifacts['build'], 2*1024**2))
        expected = create_manifest()
        _need(_same(actual, expected), 'manifest')
        for role in APK_BINDINGS:
            reader.bound(artifacts[role])
        reader.final()
        return copy.deepcopy(expected)
    except BuildRefused:
        raise
    except (OSError, ValueError, KeyError, TypeError, IndexError, RecursionError):
        raise BuildRefused('build') from None


def verify_current(admission):
    from benchmarks import owned_transcript_ui_contract as contract
    value = contract.validate_admission(admission)
    contract.revalidate_inputs(value)
    result = verify_frozen_product(value['artifacts'])
    contract.revalidate_inputs(value)
    return result
