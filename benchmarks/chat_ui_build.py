"""Fixed B55 ordinary chat APK evidence. Pure construction; no SDK or publication.

Recorded build/audit logs are not a supervised pipeline or retained raw aapt proof.
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
import struct
import subprocess
import time
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).parents[1]
SCOPE = 'chat-ui-build-v1'
APP = 'org.locallore.app'
_SPEC = {'root': "D:\\Dev\\Projects\\The Hero's Journey\\LocalLore-issue-tracking",
 'head': '8d66c24e3e575c511ca7e49d5796833446cfd1f8',
 'tested_head': 'fcf92fa30628a925da4138a8d68dd6aeef204fde',
 'source_count': 2541,
 'tested_source_count': 2540,
 'capture': 'D:\\Dev\\Experiments\\LocalLore\\2026-11-01-current-chat-apks-v1',
 'recovery': 'D:\\Dev\\Recovery\\LocalLore\\2026-11-01-current-chat-apks-v1',
 'manifest': 'D:/Dev/Experiments/LocalLore/2026-11-01-current-chat-ui-cohort-v1/chat-ui-build-v1.json',
 'records': {'build-start-v1.json': {'path': 'D:\\Dev\\Experiments\\LocalLore\\2026-11-01-current-chat-apks-v1\\build-start-v1.json',
                                     'bytes': 211,
                                     'sha256': '6d6bc5fe38f6300750af8f86072d7256b912ae925dfa4e8d19563407eb7d625b'},
             'build-terminal-v1.json': {'path': 'D:\\Dev\\Experiments\\LocalLore\\2026-11-01-current-chat-apks-v1\\build-terminal-v1.json',
                                        'bytes': 116,
                                        'sha256': '8871a84bccf524d2b3dac69ceee7b6a77031262d6f42676fb9ad5cf617c8843f'},
             'build-check-v1.log': {'path': 'D:\\Dev\\Experiments\\LocalLore\\2026-11-01-current-chat-apks-v1\\build-check-v1.log',
                                    'bytes': 11040,
                                    'sha256': 'ff05a45c12a44c5858c8cee7761207ef9abad80acd7fb822b90bb6ab3d4b3e10'},
             'closed-build-evidence-v1.json': {'path': 'D:\\Dev\\Experiments\\LocalLore\\2026-11-01-current-chat-apks-v1\\closed-build-evidence-v1.json',
                                               'bytes': 42209,
                                               'sha256': '5f5d4a57b8964c64200c14553c90f96987551d9b4c969dfee6946c8cd5c4129d'},
             'collect-closed-build-v1.py': {'path': 'D:\\Dev\\Experiments\\LocalLore\\2026-11-01-current-chat-apks-v1\\collect-closed-build-v1.py',
                                            'bytes': 9837,
                                            'sha256': 'd42207a47e716edd32dfbba2591a73629fdd9ce9603e4a75e3da3a712ce9847f'},
             'source-before-v1.json': {'path': 'D:\\Dev\\Experiments\\LocalLore\\2026-11-01-current-chat-apks-v1\\source-before-v1.json',
                                       'bytes': 494393,
                                       'sha256': '28c202525271c22e152cdbf4558fbd758f3c7ad49d5a5857b87e0d5068f48e12'},
             'tools-identity-v1.json': {'path': 'D:\\Dev\\Experiments\\LocalLore\\2026-11-01-current-chat-apks-v1\\tools-identity-v1.json',
                                        'bytes': 2265,
                                        'sha256': 'bb3c686692c35ccca8c7dab8c70dd836290959837add5e8b526186e1bf7bcb25'},
             'final-source-verification-v1.json': {'path': 'D:\\Dev\\Experiments\\LocalLore\\2026-11-01-current-chat-apks-v1\\final-source-verification-v1.json',
                                                   'bytes': 2791,
                                                   'sha256': '8992b7e556df7932c0e4ba87428bbcd59192f13df3a012d1b38de3a207057896'}},
 'recovery_records': {'preservation-receipt-v1.json': {'path': 'D:\\Dev\\Recovery\\LocalLore\\2026-11-01-current-chat-apks-v1\\preservation-receipt-v1.json',
                                                       'bytes': 40518,
                                                       'sha256': 'dfb96c61ffc34fa737be007bf4d6d8fa37482e11c1ccee040e33c193704e99db'},
                      'publication-readback-v1.json': {'path': 'D:\\Dev\\Recovery\\LocalLore\\2026-11-01-current-chat-apks-v1\\publication-readback-v1.json',
                                                       'bytes': 10967,
                                                       'sha256': '85b54b1f05dbccc3f3408a7ea7c58fd11f79dd05ed9e9206093af6cccbc50d20'},
                      'raw-source-pins-v1.json': {'path': 'D:\\Dev\\Recovery\\LocalLore\\2026-11-01-current-chat-apks-v1\\raw-source-pins-v1.json',
                                                  'bytes': 833470,
                                                  'sha256': '04af46b31b600002c84bbfd835c890886c1ef973d85685c33e9217f553a83f16'}},
 'tested_archive': {'path': 'D:\\Dev\\Experiments\\LocalLore\\2026-11-01-current-chat-apks-v1\\source-fcf92fa3.zip',
                    'bytes': 11372377,
                    'sha256': '7e7aee109a321310b3ad169dbd5e63c4e6f3c05ab72dcec7bbb9f7dbe555b5b1'},
 'canonical_archive': {'path': 'D:\\Dev\\Recovery\\LocalLore\\2026-11-01-current-chat-apks-v1\\source-canonical-v1.zip',
                       'bytes': 11377028,
                       'sha256': 'e35291cf9c2c4ebf89668a1c610f903927380e70a8f22dadbdfe0aad82848157'},
 'raw_archive': {'path': 'D:\\Dev\\Recovery\\LocalLore\\2026-11-01-current-chat-apks-v1\\source-raw-v1.zip',
                 'bytes': 11272893,
                 'sha256': '7799d2b4f80f28f8051389d80edb176eadc096321f4361b180c485a53fae64d8'},
 'apks': {'product_apk': {'path': "D:\\Dev\\Projects\\The Hero's "
                                  'Journey\\LocalLore-issue-tracking\\apps\\android\\app\\build\\outputs\\apk\\debug\\app-debug.apk',
                          'bytes': 28012688,
                          'sha256': 'a25ab00c458ed5f531935a5dcad17dd8d667fe9ed3e32059a33d77671f063591'},
          'test_apk': {'path': "D:\\Dev\\Projects\\The Hero's "
                               'Journey\\LocalLore-issue-tracking\\apps\\android\\app\\build\\outputs\\apk\\androidTest\\debug\\app-debug-androidTest.apk',
                       'bytes': 2308386,
                       'sha256': 'e6acd6ec10960f0861ce3588864ec74eb44a8b468b38a750f76cc96709cfc1a3'}},
 'suites': 50,
 'cases': 428,
 'docs_changed': ['README.md', 'docs/android/CURRENT_CHAT_APKS_2026-11-01.md'],
 'certificate': '17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564'}
SELECTORS = (('chat_ime_latest',
  'org.locallore.app.ui.ChatImeInsetsTest',
  'injectedImeKeepsLatestAboveOcclusionWithoutDoublePaddingSystemBars'),
 ('chat_ime_composer',
  'org.locallore.app.ui.ChatImeInsetsTest',
  'doubleFontComposerKeepsSendReachableAndDraftScopedAcrossInjectedImeChanges'),
 ('chat_status_history',
  'org.locallore.app.ui.ChatStatusAnnouncementTest',
  'historyReaderKeepsItsAnchorWhileCurrentBusyAndOutcomeAnnouncementsStayAvailable'),
 ('chat_status_draft',
  'org.locallore.app.ui.ChatStatusAnnouncementTest',
  'unicodeDialogueAndScopeStaySafeWhileEllipsizedNoticeKeepsFullSemantics'),
 ('chat_heading_selection',
  'org.locallore.app.ui.StoryHeadingScreenTest',
  'selectedAuthoredTitlesStayInsideTheIntroWhileDemoAndUnresolvedControlsRemainExact'),
 ('chat_heading_draft',
  'org.locallore.app.ui.StoryHeadingScreenTest',
  'titleRefreshRetainsDialogueButStoryAndBranchChangesFenceDraftsAndRetainedEdits'),
 ('chat_action_scope',
  'org.locallore.app.ui.QuickActionScopeScreenTest',
  'retainedStoryAndBranchClicksStayQuietWhileFreshControlsPreserveTheUnsentDialogue'),
 ('chat_action_availability',
  'org.locallore.app.ui.QuickActionScopeScreenTest',
  'persistentDemoAndWorkflowFencesDoNotTurnTextUnavailabilityIntoAnActionBlock'))

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


def _ordinary(path, *, cargo=False):
    path = Path(path)
    _need(path.is_absolute() and path.drive.upper() == 'D:' and path.resolve(strict=True) == path, 'path')
    for part in (path, *path.parents):
        info = part.lstat()
        _need(not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & 1024 and
              (part == path or stat.S_ISDIR(info.st_mode)), 'path')
    info = path.lstat()
    _need(stat.S_ISREG(info.st_mode), 'file')
    if cargo:
        _need(any(path in pair for pair in _cargo_pairs()) and info.st_nlink == 2, 'cargo_alias')
    else:
        _need(info.st_nlink == 1, 'file')
    return info


def _cargo_pairs():
    return tuple((Path(_SPEC['root']) / ('apps/android/app/build/rust-target/'+target+
        '/release/liblocallore_android.so'), Path(_SPEC['root']) / ('apps/android/app/build/rust-target/'+target+
        '/release/deps/liblocallore_android.so')) for target in ('x86_64-linux-android','aarch64-linux-android'))


def _cargo_pair(path):
    pairs = [pair for pair in _cargo_pairs() if path in pair]
    _need(len(pairs) == 1, 'cargo_alias')
    pair = pairs[0]
    left, right = (_ordinary(name, cargo=True) for name in pair)
    _need((left.st_dev, left.st_ino, left.st_size, left.st_mtime_ns) ==
          (right.st_dev, right.st_ino, right.st_size, right.st_mtime_ns), 'cargo_alias')
    return pair


def _stamp(info):
    return tuple(getattr(info, key) for key in ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns', 'st_nlink', 'st_mode'))


class _Reader:
    def __init__(self):
        self.deadline = time.monotonic() + 120
        self.checked = {}

    def raw(self, path, cap=64*1024**2):
        return self._raw(path, cap, cargo=False)

    def _raw(self, path, cap, *, cargo):
        _need(time.monotonic() < self.deadline, 'deadline')
        path = Path(path)
        before = _ordinary(path, cargo=cargo)
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
        _need(len(raw) == before.st_size and _stamp(before) == _stamp(_ordinary(path, cargo=cargo)), 'changed')
        pin = dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        if path in self.checked:
            _need(_same(pin, self.checked[path][0]) and _stamp(before) == self.checked[path][1] and
                  cargo is self.checked[path][2], 'changed')
        self.checked[path] = (pin, _stamp(before), cargo)
        return bytes(raw)

    def pin(self, path):
        self.raw(path)
        return copy.deepcopy(self.checked[Path(path)][0])

    def bound(self, value, cap=64*1024**2):
        _binding(value)
        raw = self.raw(value['path'], cap)
        _need(_same(value, self.checked[Path(value['path'])][0]), 'binding')
        return raw

    def cargo_release(self, value):
        """Only _native uses this exact two-name Cargo output role; not generic IO."""
        _binding(value)
        path = Path(value['path'])
        pair = _cargo_pair(path)
        _need(path == pair[0], 'cargo_alias')
        raw = self._raw(path, 32*1024**2, cargo=True)
        alias = self._raw(pair[1], 32*1024**2, cargo=True)
        _need(raw == alias and _same(value, self.checked[path][0]), 'cargo_alias')
        _cargo_pair(path)
        return raw

    def final(self):
        for path in list(self.checked):
            cargo = self.checked[path][2]
            if cargo:
                _cargo_pair(path)
            self._raw(path, 64*1024**2, cargo=cargo)
            if cargo:
                _cargo_pair(path)


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


def _root():
    return Path(_SPEC['root'])


def _git(args):
    _need(args in (['rev-parse', 'HEAD'], ['status', '--porcelain', '--untracked-files=all'],
                  ['ls-files', '-z']), 'git')
    root = _root()
    _need(root.is_absolute() and root.drive.upper() == 'D:' and root.resolve(strict=True) == root, 'path')
    for part in (root, *root.parents):
        info = part.lstat()
        _need(stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode) and
              not getattr(info, 'st_file_attributes', 0) & 1024, 'path')
    answer = subprocess.run(['git', '--no-optional-locks', '-C', str(root)] + args,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15,
        env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'))
    _need(answer.returncode == 0 and answer.stderr == b'', 'source')
    return answer.stdout


def _source(reader):
    _need(_git(['rev-parse', 'HEAD']).decode('ascii').strip() == _SPEC['head'] and
          _git(['status', '--porcelain', '--untracked-files=all']) == b'', 'source')
    names = _git(['ls-files', '-z']).decode('utf-8').split('\0')
    _need(names[-1] == '' and len(names[:-1]) == len(set(names[:-1])) == _SPEC['source_count'], 'source')
    result = {}
    for name in names[:-1]:
        _relative(name)
        pin = reader.pin(_root() / name)
        result[name] = dict(bytes=pin['bytes'], sha256=pin['sha256'])
    return result


def _rows(rows, *, full_paths=False):
    _need(type(rows) is list and 0 < len(rows) <= 4096, 'source')
    result = {}
    for row in rows:
        _keys(row, ('relative', 'path', 'bytes', 'sha256') if full_paths else ('path', 'bytes', 'sha256'))
        name = row['relative'] if full_paths else row['path']
        _relative(name)
        _need(name not in result, 'source')
        expected = str(_root() / name)
        _binding(dict(path=expected, bytes=row['bytes'], sha256=row['sha256']))
        if full_paths:
            _need(Path(row['path']) == Path(expected), 'source')
        result[name] = dict(bytes=row['bytes'], sha256=row['sha256'])
    return result


def _archive(reader, binding, expected, head=None):
    with zipfile.ZipFile(io.BytesIO(reader.bound(binding))) as archive:
        entries = archive.infolist()
        _need(len(entries) <= 8192 and len({e.filename for e in entries}) == len(entries) and
              sum(e.file_size for e in entries) <= 64*1024**2, 'archive')
        _need(archive.comment == (head.encode('ascii') if head else b''), 'archive')
        found = {}
        for entry in entries:
            _relative(entry.filename.rstrip('/'))
            kind = stat.S_IFMT(entry.external_attr >> 16)
            _need(not entry.flag_bits & 1 and kind in (0, stat.S_IFDIR, stat.S_IFREG), 'archive')
            if entry.is_dir():
                _need(entry.file_size == 0, 'archive')
                continue
            _need(entry.file_size <= 8*1024**2, 'archive')
            raw = archive.read(entry)
            found[entry.filename] = dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        _need(_same(found, expected), 'source')


def _sources(reader, current, records, recovery):
    before = _json(records['source-before-v1.json'])
    _keys(before, ('head', 'files', 'eolOnlyDifferences', 'canonicalSourceZip'))
    tested = _rows(before['files'])
    _need(before['head'] == _SPEC['tested_head'] and len(tested) == _SPEC['tested_source_count'] and
          before['eolOnlyDifferences'] == [] and _same(before['canonicalSourceZip'], _SPEC['tested_archive']), 'source')
    final = _json(records['final-source-verification-v1.json'])
    _need(final['head'] == _SPEC['head'] and final['testedHead'] == _SPEC['tested_head'] and
          type(final['trackedFiles']) is int and final['trackedFiles'] == _SPEC['source_count'] and
          final['eolOnlyDifferences'] == [] and _same(final['canonical'], _SPEC['canonical_archive']) and
          _same(final['raw'], _SPEC['raw_archive']) and final['admissionManifest'] is False and
          final['androidRuntimeExecuted'] is False, 'source')
    raw = _rows(_json(recovery['raw-source-pins-v1.json']), full_paths=True)
    _need(_same(current, raw), 'source')
    changed = sorted(name for name in set(tested) | set(current) if tested.get(name) != current.get(name))
    _need(changed == sorted(_SPEC['docs_changed']) and set(current) - set(tested) == {_SPEC['docs_changed'][1]} and
          not set(tested) - set(current), 'source')
    _archive(reader, _SPEC['tested_archive'], tested, _SPEC['tested_head'])
    _archive(reader, _SPEC['canonical_archive'], current, _SPEC['head'])
    _archive(reader, _SPEC['raw_archive'], current)
    return dict(root=str(_root()), head=_SPEC['head'], tested_head=_SPEC['tested_head'],
        current_raw_sources=current, tested_raw_map=_SPEC['records']['source-before-v1.json'],
        tested_canonical_archive=_SPEC['tested_archive'], canonical_archive=_SPEC['canonical_archive'],
        raw_archive=_SPEC['raw_archive'], raw_pins=_SPEC['recovery_records']['raw-source-pins-v1.json'],
        documentation_only_changes=changed)


def _preservation(reader, records, recovery):
    receipt = _json(recovery['preservation-receipt-v1.json'])
    _keys(receipt, ('head', 'source', 'controlsBytes', 'controls'))
    _need(receipt['head'] == _SPEC['head'] and
          _same(receipt['source'], _json(records['final-source-verification-v1.json'])), 'preservation')
    _need(type(receipt['controls']) is list and len(receipt['controls']) == 64 and
          type(receipt['controlsBytes']) is int, 'preservation')
    seen, total = set(), 0
    capture = Path(_SPEC['capture'])
    for row in receipt['controls']:
        _keys(row, ('original', 'copy'))
        original, copied = row['original'], row['copy']
        _binding(original); _binding(copied)
        name = Path(original['path']).relative_to(capture).as_posix()
        _relative(name)
        _need(name not in seen and Path(copied['path']) == Path(_SPEC['recovery']) / 'controls-v1' / name, 'preservation')
        seen.add(name)
        _need(reader.bound(original) == reader.bound(copied), 'preservation')
        total += original['bytes']
    _need(total == receipt['controlsBytes'], 'preservation')
    required = set(_SPEC['records']) | {'source-fcf92fa3.zip'}
    _need(required <= seen, 'preservation')
    publication = _json(recovery['publication-readback-v1.json'])
    _need(publication['head'] == _SPEC['head'] and publication['testedHead'] == _SPEC['tested_head'] and
          _same(publication['limitations'], dict(androidRuntimeExecuted=False, admissionManifest=False,
              innerRawAuditTools=False, sibling317Included=False, fullSupervisedPipeline=False)), 'preservation')


def _xml(raw):
    _need(len(raw) <= 2*1024**2 and b'<!DOCTYPE' not in raw.upper() and b'<!ENTITY' not in raw.upper(), 'xml')
    return ET.fromstring(raw)


def _cases(raw):
    suite = _xml(raw)
    cases = suite.findall('testcase')
    _need(suite.tag == 'testsuite' and list(suite.iter('testsuite')) == [suite] and
          list(suite.iter('testcase')) == cases and int(suite.attrib['tests']) == len(cases), 'jvm')
    _need(all(int(suite.attrib[k]) == 0 for k in ('failures', 'errors', 'skipped')) and
          not any(list(suite.iter(tag)) for tag in ('failure', 'error', 'skipped')), 'jvm')
    _need(all(case.get('classname') == suite.get('name') and case.get('name') for case in cases), 'jvm')
    result = [(case.get('classname'), case.get('name')) for case in cases]
    _need(len(result) == len(set(result)), 'jvm')
    return result


def _reports(reader, evidence):
    junit = evidence['junit']
    _keys(junit, ('counts', 'uniqueCases', 'suites', 'reports'))
    _need(_same(junit['counts'], dict(tests=_SPEC['cases'], failures=0, errors=0, skipped=0)) and
          type(junit['uniqueCases']) is int and junit['uniqueCases'] == _SPEC['cases'] and
          type(junit['suites']) is int and junit['suites'] == _SPEC['suites'] and
          type(junit['reports']) is list and len(junit['reports']) == _SPEC['suites'], 'jvm')
    report_root = _root() / 'apps/android/app/build/test-results/testDebugUnitTest'
    seen, identities = set(), []
    for row in junit['reports']:
        _keys(row, ('original', 'copy'))
        source, copied = row['original'], row['copy']
        name = Path(source['path']).name
        _need(Path(source['path']).parent == report_root and name not in seen and name.startswith('TEST-') and
              name.endswith('.xml') and Path(copied['path']) == Path(_SPEC['capture']) / 'reports-v1' / name, 'report')
        seen.add(name)
        raw = reader.bound(source, 2*1024**2)
        _need(reader.bound(copied, 2*1024**2) == raw and name == 'TEST-'+str(_xml(raw).get('name'))+'.xml', 'report')
        identities.extend(_cases(raw))
    _need(set(p.name for p in report_root.glob('TEST-*.xml')) == seen and
          len(identities) == len(set(identities)) == _SPEC['cases'], 'jvm')
    lint = _root() / 'apps/android/app/build/reports/lint-results-debug.xml'
    raw = reader.raw(lint, 2*1024**2)
    _need(reader.raw(Path(_SPEC['capture']) / 'reports-v1' / lint.name, 2*1024**2) == raw, 'lint')
    tree = _xml(raw)
    counts = Counter((v.get('id'), v.get('severity')) for v in tree.findall('issue'))
    expected = Counter({('GradleDependency', 'Warning'): 1, ('AutoboxingStateCreation', 'Hint'): 1})
    _need(tree.tag == 'issues' and counts == expected and
          Counter((v['id'], v['severity']) for v in evidence['lint']) == expected, 'lint')
    return dict(suites=_SPEC['suites'], cases=_SPEC['cases'], reports=junit['reports']), dict(binding=reader.pin(lint),
        issues=[dict(id=k[0], severity=k[1], count=v) for k, v in sorted(counts.items())])


def _parsers(reader):
    # Load only the fixed, source-compared pure decoders, never a tool entrypoint.
    groups = {'scripts/audit_physical_model_apk.py': ('Dex', 'dex_classes'),
              'scripts/audit_apk.py': ('require', 'elf_alignments')}
    namespace = dict(struct=struct, re=re, zipfile=zipfile, AuditError=BuildRefused)
    pins = {}
    for relative, names in groups.items():
        nodes = []
        for root in (_root(), ROOT):
            raw = reader.raw(root / relative)
            tree = ast.parse(raw)
            selected = [n for n in tree.body if isinstance(n, (ast.ClassDef, ast.FunctionDef)) and n.name in names]
            _need({n.name for n in selected} == set(names), 'parser')
            nodes.append(selected)
        _need([ast.dump(n, include_attributes=False) for n in nodes[0]] ==
              [ast.dump(n, include_attributes=False) for n in nodes[1]], 'parser')
        exec(compile(ast.Module(body=nodes[1], type_ignores=[]), relative, 'exec'), namespace)
        pins[relative] = dict(product=reader.pin(_root()/relative), launcher=reader.pin(ROOT/relative))
    from benchmarks import android_instrumentation_evidence as instrumentation
    relative = 'benchmarks/android_instrumentation_evidence.py'
    _need(Path(instrumentation.__file__).resolve() == ROOT/relative and
          reader.raw(_root()/relative) == reader.raw(ROOT/relative), 'parser')
    pins[relative] = dict(product=reader.pin(_root()/relative), launcher=reader.pin(ROOT/relative))
    return namespace, instrumentation, pins


def _audits_and_dex(reader, records, evidence, parser, instrumentation):
    text = records['build-check-v1.log'].decode('utf-8-sig')
    lines = text.splitlines()
    commands = [ast.literal_eval(line[2:]) for line in lines if line.startswith('+ ')]
    python = commands[1][0] if len(commands) == 3 and type(commands[1]) is list and commands[1] else None
    _need(type(python) is str and Path(python).name.lower() == 'python.exe' and Path(python).drive.upper() == 'C:', 'command')
    app = _SPEC['apks']['product_apk']; test = _SPEC['apks']['test_apk']
    expected = [[r'C:\Program Files\Java\jdk-21\bin\java.exe', '-classpath',
        str(_root()/'apps/android/gradle/wrapper/gradle-wrapper.jar'), 'org.gradle.wrapper.GradleWrapperMain',
        ':app:assembleDebug', ':app:assembleDebugAndroidTest', ':app:testDebugUnitTest', ':app:lintDebug',
        '--no-daemon', '--console=plain', '-Pandroid.builder.sdkDownload=false', '--offline'],
        [python, str(_root()/'scripts/audit_apk.py'), app['path']],
        [python, str(_root()/'scripts/audit_instrumentation_apk.py'), app['path'], test['path']]]
    _need(_same(commands, expected), 'command')
    for task in ('buildRustAndroid', 'compileDebugAndroidTestKotlin', 'testDebugUnitTest', 'lintDebug',
                 'assembleDebug', 'assembleDebugAndroidTest'):
        heading = '> Task :app:'+task
        rows = [line for line in lines if line == heading or line.startswith(heading+' ')]
        _need(rows and all(row == heading for row in rows), 'freshness')
    _need('81 actionable tasks: 81 executed' in lines and 'BUILD SUCCESSFUL in 1m 55s' in lines and
          'FROM-CACHE' not in text and 'BUILD FAILED' not in text, 'build')
    for target, abi in (('x86_64-linux-android', 'x86_64'), ('aarch64-linux-android', 'arm64-v8a')):
        _need('Building LocalLore Rust JNI: '+target+' -> '+abi in lines, 'native')
    objects = []
    decoder = json.JSONDecoder()
    # The complete log is byte-pinned; decode the two actual producer objects.
    for match in re.finditer(r'(?m)^\{', text):
        value, end = decoder.raw_decode(text, match.start())
        objects.append(_json(text[match.start():end].encode()))
    _need(len(objects) == 2 and _same(objects, [evidence['productAudit'], evidence['pairAudit']]), 'audit')
    product, pair = objects
    _keys(product, ('status', 'permissions', 'libraries'))
    _keys(pair, ('app', 'test', 'certificate_sha256', 'package', 'status', 'test_package', 'test_permissions'))
    _need(product['status'] == pair['status'] == 'passed' and pair['package'] == APP and
          pair['test_package'] == APP+'.test' and pair['test_permissions'] == ['android.permission.REORDER_TASKS'] and
          pair['certificate_sha256'] == _SPEC['certificate'] and
          product['permissions'] == [APP+'.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION'], 'audit')
    for role, key in (('product_apk', 'app'), ('test_apk', 'test')):
        _need(_same(pair[key], {k:_SPEC['apks'][role][k] for k in ('bytes','sha256')}), 'audit')
        raw = reader.bound(_SPEC['apks'][role])
        copied = Path(_SPEC['capture'])/'apks-v1'/Path(_SPEC['apks'][role]['path']).name
        _need(reader.raw(copied) == raw and _same(evidence['apkCopies'][0 if key=='app' else 1], reader.pin(copied)), 'apk')
    app_classes = parser['dex_classes'](Path(app['path']))
    test_classes = parser['dex_classes'](Path(test['path']))
    expected_classes = {}
    for _, klass, method in SELECTORS:
        expected_classes.setdefault(klass, []).append(method)
    definitions = []
    for klass, methods in expected_classes.items():
        source = _root()/'apps/android/app/src/androidTest/java'/(klass.replace('.', '/')+'.kt')
        reader.pin(source)
        _need(instrumentation.test_roster(source) == methods, 'roster')
        descriptor = ('L'+klass.replace('.', '/')+';').encode('ascii')
        _need(descriptor not in app_classes and descriptor in test_classes, 'dex')
        flags, members = test_classes[descriptor]
        _need(flags & 1 and not flags & (0x200 | 0x400), 'dex')
        annotated = [name.decode('ascii') for name, _, _, junit in members if junit]
        _need(len(annotated) == len(methods) and set(annotated) == set(methods), 'dex')
        for method in methods:
            found = [(proto, flags, junit) for name, proto, flags, junit in members if name == method.encode('ascii')]
            _need(len(found) == 1 and found[0][0] == (b'V',0) and found[0][1] & 1 and
                  not found[0][1] & (8 | 0x100 | 0x400) and found[0][2] is True, 'dex')
            definitions.append(dict(selector=klass+'#'+method, public=True, static=False, abstract=False,
                                    native=False, voidZeroArgs=True, junitAnnotation=True))
    _need(_same(definitions, evidence['definedUiMethods']), 'dex')
    return {role:dict(binding=copy.deepcopy(pin), package=APP+('.test' if role=='test_apk' else ''),
                      certificate_sha256=_SPEC['certificate']) for role,pin in _SPEC['apks'].items()}, product


def _native(reader, evidence, product, parser):
    rows = evidence['nativeJoins']
    _need(type(rows) is list and [r['abi'] for r in rows] == ['x86_64', 'arm64-v8a'], 'native')
    root = _root()/'apps/android/app/build'
    result = []
    with zipfile.ZipFile(io.BytesIO(reader.bound(_SPEC['apks']['product_apk']))) as archive:
        entries = archive.infolist()
        names = [e.filename for e in entries]
        _need(len(names) == len(set(names)) <= 4096, 'apk')
        libraries = []
        for entry in entries:
            _relative(entry.filename.rstrip('/'))
            _need(not entry.flag_bits & 1 and stat.S_IFMT(entry.external_attr >> 16) in (0,stat.S_IFREG,stat.S_IFDIR), 'apk')
            if not entry.filename.endswith('.so'):
                continue
            parts = entry.filename.split('/')
            _need(len(parts) == 3 and parts[0] == 'lib' and parts[1] in ('x86_64','arm64-v8a') and
                  entry.compress_type == zipfile.ZIP_STORED and 0 < entry.file_size <= 32*1024**2, 'native')
            with archive.open(entry) as stream:
                raw = stream.read()
            # APK local-header data alignment is distinct from ELF segment alignment.
            archive.fp.seek(entry.header_offset)
            header = archive.fp.read(30)
            _need(header[:4] == b'PK\x03\x04' and len(header) == 30, 'apk')
            name_size, extra_size = struct.unpack_from('<HH', header, 26)
            _need((entry.header_offset+30+name_size+extra_size) % 16384 == 0, 'native')
            libraries.append(dict(entry=entry.filename, elf_load_alignment=parser['elf_alignments'](raw,
                62 if parts[1]=='x86_64' else 183)))
        _need(_same(sorted(libraries, key=lambda x:x['entry']), sorted(product['libraries'], key=lambda x:x['entry'])) and
              {r['entry'] for r in libraries} == {'lib/'+abi+'/'+name for abi in ('x86_64','arm64-v8a')
                  for name in ('liblocallore_android.so','libandroidx.graphics.path.so')}, 'native')
        for row, (target, abi) in zip(rows, (('x86_64-linux-android','x86_64'),('aarch64-linux-android','arm64-v8a'))):
            _keys(row, ('abi','release','generated','merged','stripped','apkEntry','apkBytes','apkSHA256','stripStageHasDifferentBytes'))
            paths = {'release':root/f'rust-target/{target}/release/liblocallore_android.so',
                'generated':root/f'generated/rustJniLibs/{abi}/liblocallore_android.so',
                'merged':root/f'intermediates/merged_native_libs/debug/mergeDebugNativeLibs/out/lib/{abi}/liblocallore_android.so',
                'stripped':root/f'intermediates/stripped_native_libs/debug/stripDebugDebugSymbols/out/lib/{abi}/liblocallore_android.so'}
            raw = {}
            for stage, path in paths.items():
                _need(Path(row[stage]['path']) == path, 'native')
                raw[stage] = reader.cargo_release(row[stage]) if stage == 'release' else reader.bound(row[stage])
            _need(raw['release'] == raw['generated'] == raw['merged'] and
                  row['apkEntry'] == f'lib/{abi}/liblocallore_android.so' and
                  type(row['apkBytes']) is int and row['apkBytes'] == len(raw['stripped']) and
                  row['apkSHA256'] == hashlib.sha256(raw['stripped']).hexdigest() and
                  archive.read(row['apkEntry']) == raw['stripped'] and
                  row['stripStageHasDifferentBytes'] is (raw['release'] != raw['stripped']), 'native')
            observed = copy.deepcopy(row)
            alias = paths['release'].parent/'deps/liblocallore_android.so'
            observed['current_cargo_alias'] = dict(scope='current-read-only-cargo-output-observation',
                release=copy.deepcopy(row['release']), deps=copy.deepcopy(reader.checked[alias][0]),
                links_per_name=2, historical_b55_alias_observation=False)
            result.append(observed)
    return result


def _create_manifest():
    reader = _Reader()
    current = _source(reader)
    records = {name:reader.bound(pin, 2*1024**2) for name,pin in _SPEC['records'].items()}
    recovery = {name:reader.bound(pin, 2*1024**2) for name,pin in _SPEC['recovery_records'].items()}
    source = _sources(reader, current, records, recovery)
    _preservation(reader, records, recovery)
    evidence = _json(records['closed-build-evidence-v1.json'])
    _need(type(evidence['version']) is int and evidence['version'] == 1 and evidence['head'] == _SPEC['tested_head'] and
          type(evidence['trackedSourcesUnchanged']) is int and evidence['trackedSourcesUnchanged'] == _SPEC['tested_source_count'] and
          evidence['androidRuntimeExecuted'] is False and evidence['admissionManifest'] is False and
          type(evidence['dexReaderProcessCalls']) is int and evidence['dexReaderProcessCalls'] == 0 and
          type(evidence['dexReaderSocketCalls']) is int and evidence['dexReaderSocketCalls'] == 0, 'receipt')
    terminal = _json(records['build-terminal-v1.json'])
    _keys(terminal, ('androidRuntimeExecuted','elapsedSeconds','nativeIncluded','exit'))
    _need(terminal['androidRuntimeExecuted'] is False and terminal['nativeIncluded'] is True and
          type(terminal['exit']) is int and terminal['exit'] == 0 and type(terminal['elapsedSeconds']) in (int,float) and
          0 < terminal['elapsedSeconds'] < 900 and _same(terminal,evidence['buildTerminal']), 'terminal')
    start = _json(records['build-start-v1.json'])
    _keys(start, ('deviceOperations','ordinaryProfile','offline','nativeIncluded','head','started'))
    _need(start['deviceOperations'] is False and start['ordinaryProfile'] is True and start['offline'] is True and
          start['nativeIncluded'] is True and start['head'] == _SPEC['tested_head'] and type(start['started']) is str, 'start')
    _need(_same(evidence['buildLog'], _SPEC['records']['build-check-v1.log']) and
          _same(evidence['dexReader'], dict(path=str(_root()/'scripts/audit_physical_model_apk.py'),
              **current['scripts/audit_physical_model_apk.py'])), 'receipt')
    parser, instrumentation, parser_pins = _parsers(reader)
    apks, product = _audits_and_dex(reader, records, evidence, parser, instrumentation)
    jvm, lint = _reports(reader, evidence)
    native = _native(reader, evidence, product, parser)
    _need(_same(_source(reader), current), 'source')
    reader.final()
    return dict(version=1, scope=SCOPE, product_source=source, apks=apks, jvm=jvm, lint=lint,
        native_chains=native, roster=[list(row) for row in SELECTORS], parser_sources=parser_pins,
        recorded_execution=dict(scope='b55-recorded-gradle-and-audits-v1', records=copy.deepcopy(_SPEC['records']),
            recovery_records=copy.deepcopy(_SPEC['recovery_records']), historical_full_raw_source_map=True,
            historical_supervised_pipeline=False, historical_inner_raw_aapt=False,
            historical_executable_byte_pins=False, ui_runtime_executed=False))


def create_manifest():
    """Return validated data for one fixed build. Never publish or invoke SDK tools."""
    try:
        return _create_manifest()
    except BuildRefused:
        raise
    except (OSError, ValueError, KeyError, TypeError, IndexError, StopIteration, SyntaxError,
            RecursionError, UnicodeError, zipfile.BadZipFile, ET.ParseError, struct.error, subprocess.SubprocessError):
        raise BuildRefused('build') from None


def _artifacts(artifacts):
    _keys(artifacts, ('build','product_apk','test_apk'))
    for pin in artifacts.values():
        _binding(pin)
    _need(Path(artifacts['build']['path']) == Path(_SPEC['manifest']) and artifacts['build']['bytes'] <= 2*1024**2 and
          all(_same(artifacts[role], pin) for role,pin in _SPEC['apks'].items()), 'artifacts')


def verify_frozen_product(artifacts):
    try:
        _artifacts(artifacts)
        reader = _Reader()
        actual = _json(reader.bound(artifacts['build'], 2*1024**2))
        expected = create_manifest()
        _need(_same(actual, expected), 'manifest')
        for role in _SPEC['apks']:
            reader.bound(artifacts[role])
        reader.final()
        return copy.deepcopy(expected)
    except BuildRefused:
        raise
    except (OSError, ValueError, KeyError, TypeError, IndexError, RecursionError):
        raise BuildRefused('build') from None


def verify_current(admission):
    from benchmarks import owned_chat_ui_contract as contract
    value = contract.validate_admission(admission)
    contract.revalidate_inputs(value)
    result = verify_frozen_product(value['artifacts'])
    contract.revalidate_inputs(value)
    return result
