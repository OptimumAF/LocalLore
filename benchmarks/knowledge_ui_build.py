"""B88 fixed byte attestation; no publication or target execution.
Recorded audits are checked by bytes and joins; their tools are never rerun.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess

from benchmarks import library_ui_build as _shared

BuildRefused = _shared.BuildRefused
_Reader = _shared._Reader  # Unmodified guarded reader; cargo=True is never used.
_json = _shared._json
_same = _shared._same
_binding = _shared._binding
_need = _shared._need
_keys = _shared._keys

SCOPE = 'knowledge-ui-build-v1'
MODE = 'fixed-b88-byte-attestation-v1'
BASELINE_PATH = Path('D:/Worktrees/LocalLore-original-input-compose-review-v1/benchmarks/knowledge_ui_build_baseline.json')
BASELINE_BYTES = 55535
BASELINE_SHA256 = 'c1570a1552bf1579544682eeeb9593254ba0d3b30884e1680c626fa5e0c209fc'
SOURCE_ENCODING = 'Exact recorded raw worktree bytes; Git identity never authorizes newline normalization'
_FIXED = dict(
    root=str(Path('D:/Worktrees/LocalLore-record-query2-fixtures-v1')),
    capture=str(Path('D:/Dev/Experiments/LocalLore/2026-11-02-knowledge-ui-build-v1')),
    recovery=str(Path('D:/Dev/Recovery/LocalLore/2026-11-02-knowledge-ui-build-v1')),
    manifest=str(Path('D:/Dev/Experiments/LocalLore/2026-11-02-knowledge-ui-build-v1/knowledge-ui-build-v1.json')),
    head='286c0905613e9bbff2d69796155105339000eceb',
    source_count=2608, preservation_pairs=74,
    apks=dict(
        product_apk=dict(path=str(Path('D:/Worktrees/LocalLore-record-query2-fixtures-v1/apps/android/app/build/outputs/apk/debug/app-debug.apk')),
            bytes=28398622, sha256='0b93c6af0772ff6216a0dcbeb2f8b19b1564129f3855336ced7dcafbfca662cd'),
        test_apk=dict(path=str(Path('D:/Worktrees/LocalLore-record-query2-fixtures-v1/apps/android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk')),
            bytes=2645072, sha256='3241aaff3c42fc6c155f04da40cae88aa54e39cd68c10f7cb5178a0b77a9c5db')),
    native={
        'arm64-v8a': dict(path=str(Path('D:/Worktrees/LocalLore-record-query2-fixtures-v1/apps/android/app/build/generated/rustJniLibs/arm64-v8a/liblocallore_android.so')),
            bytes=11244368, sha256='057669ea127c40ce82a93e7818897c5b718342881477f34f096beda8c8815e55'),
        'x86_64': dict(path=str(Path('D:/Worktrees/LocalLore-record-query2-fixtures-v1/apps/android/app/build/generated/rustJniLibs/x86_64/liblocallore_android.so')),
            bytes=11574528, sha256='1b7fc490ad69e3edea660869a7446330a11ad35c90b070255c4e6ed7d11111d3')},
)
ROSTER = [
    ['knowledge_labels', 'org.locallore.app.ui.KnowledgeRecordFilterScreenTest',
     'exactlyFiveKnowledgeFacetsExposeLiteralLabelsSelectionAndFortyEightDpTargetsOnlyInKnowledge'],
    ['knowledge_replaced', 'org.locallore.app.ui.KnowledgeRecordFilterScreenTest',
     'retainedRealFacetAndCloseActionsCannotRetargetDifferentOrEqualDistinctSuppliedViews'],
    ['knowledge_remount', 'org.locallore.app.ui.KnowledgeRecordFilterScreenTest',
     'removedAndRemountedSameStateCannotReviveOldFacetOrCloseButFreshActionsStillWork'],
    ['knowledge_text', 'org.locallore.app.ui.KnowledgeRecordFilterScreenTest',
     'doubledFontKeepsEveryFacetAndUnchangedOriginSourceAndCloseReachableInTheActualDialog'],
]
_FACTS = dict(
    jvm_cases=579, jvm_suites=69, jvm_failures=0, jvm_errors=0, jvm_skips=0,
    selected_runtime_methods=4, compiled_ui_methods=4,
    android_runtime_executed=False, model_material=False,
    feature_acceptance=False, fresh_native_compilation=False,
    deep_semantic_review_repeated=False, full_tool_binary_provenance=False,
    full_cache_or_TEMP_meter=False,
)
# Fixed recorded facts from final android-v2 output and dex-evidence-v1.json.
# The separately sealed DEX record supplies the definition evidence; this module
# never invokes a DEX, ELF, signature or package tool.
_RECORDED_AUDIT = dict(status='passed', package='org.locallore.app',
    test_package='org.locallore.app.test',
    certificate_sha256='17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564',
    product_permissions=['org.locallore.app.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION'],
    test_permissions=['android.permission.REORDER_TASKS'],
    product_definitions=[], test_definitions=copy.deepcopy(ROSTER),
    libraries=[dict(entry='lib/'+abi+'/'+name, elf_load_alignment=[16384,16384,16384])
        for abi in ('arm64-v8a','x86_64')
        for name in ('libandroidx.graphics.path.so','liblocallore_android.so')])
_ENV_KEYS = ('TEMP','TMP','TMPDIR','JAVA_HOME','ANDROID_HOME','ANDROID_SDK_ROOT',
    'CARGO_HOME','GRADLE_USER_HOME','CARGO_NET_OFFLINE','RUSTUP_AUTO_INSTALL',
    'PYTHONDONTWRITEBYTECODE','CARGO_TARGET_DIR','CARGO_PROFILE_DEV_DEBUG',
    'CARGO_PROFILE_TEST_DEBUG','CARGO_BUILD_JOBS','JAVA_TOOL_OPTIONS')


def _integer(value, expected=None):
    _need(type(value) is int and value >= 0 and (expected is None or value == expected), 'count')


def _pin_path(pin, path):
    _binding(pin)
    _need(pin['path'] == str(path), 'binding_path')


def _paths():
    out = Path(_FIXED['capture'])
    phase = out/'android-v2'
    return dict(request=phase/'request-v1.json', owner=phase/'owner-result-v1.json',
        terminal=phase/'terminal-v1.json', command_terminal=phase/'command-terminal-v1.json',
        stdout=phase/'owner-stdout-v1.bin', stderr=phase/'owner-stderr-v1.bin',
        reports=phase/'report-preservation-v1.json', helper=out/'run-build-v1.py',
        actual_child=phase/'actual-child-v1.json', command_child=phase/'command-child-v1.json',
        jvm_execution=out/'jvm-evidence-v1.json', dex=out/'dex-evidence-v1.json')


def _git(args):
    _need(args in (['rev-parse','HEAD'], ['status','--porcelain','--untracked-files=all'],
                  ['ls-files','-z']), 'git')
    root = Path(_FIXED['root'])
    _need(root.drive.upper() == 'D:' and root.resolve(strict=True) == root, 'path')
    for path in (root, *root.parents):
        stamp = path.lstat()
        _need(stat.S_ISDIR(stamp.st_mode) and not stat.S_ISLNK(stamp.st_mode) and
              not getattr(stamp, 'st_file_attributes', 0) & 1024, 'path')
    result = subprocess.run(['git','--no-optional-locks','-C',str(root),*args],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15, check=False,
        env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'))
    _need(type(result.returncode) is int and result.returncode == 0 and result.stderr == b'', 'git')
    return result.stdout


def _git_identity():
    _need(_git(['rev-parse','HEAD']).decode('ascii').strip() == _FIXED['head'] and
          _git(['status','--porcelain','--untracked-files=all']) == b'', 'source')


def _audit_facts(value):
    _keys(value, ('status','package','test_package','certificate_sha256',
        'product_permissions','test_permissions','product_definitions','test_definitions',
        'libraries'))
    _need(value['status'] == 'passed' and value['package'] == 'org.locallore.app' and
          value['test_package'] == 'org.locallore.app.test' and
          value['product_permissions'] == ['org.locallore.app.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION'] and
          value['test_permissions'] == ['android.permission.REORDER_TASKS'] and
          value['product_definitions'] == [] and _same(value['test_definitions'], ROSTER), 'audit')
    _need(type(value['certificate_sha256']) is str and
          re.fullmatch('[0-9a-f]{64}', value['certificate_sha256']), 'audit')
    expected = ['lib/'+abi+'/'+name for abi in ('arm64-v8a','x86_64')
                for name in ('libandroidx.graphics.path.so','liblocallore_android.so')]
    _need(type(value['libraries']) is list and len(value['libraries']) == 4, 'audit')
    for row, name in zip(value['libraries'], expected):
        _keys(row, ('entry','elf_load_alignment'))
        _need(row['entry'] == name and type(row['elf_load_alignment']) is list and
              len(row['elf_load_alignment']) > 0, 'audit')
        for alignment in row['elf_load_alignment']:
            _integer(alignment, 16384)


def _baseline(reader):
    identity = dict(path=str(BASELINE_PATH), bytes=BASELINE_BYTES, sha256=BASELINE_SHA256)
    _binding(identity)  # Explicit None placeholders fail closed before any read.
    _need(type(_RECORDED_AUDIT) is dict, 'unfrozen')
    _audit_facts(_RECORDED_AUDIT)
    value = reader.json(identity)
    _keys(value, ('version','scope','product','evidence','artifacts','native',
                  'bindings','facts','instrumentations'))
    _integer(value['version'], 1)
    _need(value['scope'] == 'knowledge-ui-build-baseline-v1' and
          _same(value['instrumentations'], ROSTER), 'baseline')
    product = value['product']
    _keys(product, ('root','head','source_count','source_encoding',
                    'source_before','source_after','source_archive'))
    _need(product['root'] == _FIXED['root'] and product['head'] == _FIXED['head'] and
          product['source_encoding'] == SOURCE_ENCODING, 'baseline')
    _integer(product['source_count'], _FIXED['source_count'])
    phase = Path(_FIXED['capture'])/'android-v2'
    for role in ('before','after'):
        _pin_path(product['source_'+role], phase/('source-'+role+'-v1.json'))
    _pin_path(product['source_archive'], Path(_FIXED['capture'])/('source-'+_FIXED['head']+'.zip'))
    _keys(value['evidence'], _paths())
    for role, path in _paths().items():
        _pin_path(value['evidence'][role], path)
    _keys(value['artifacts'], ('product_apk','test_apk'))
    _keys(value['native'], ('arm64-v8a','x86_64'))
    _need(_same(value['artifacts'], _FIXED['apks']) and
          _same(value['native'], _FIXED['native']), 'baseline')
    for pin in (*value['artifacts'].values(), *value['native'].values()):
        _binding(pin)
    facts = dict(_FACTS, package_audit=copy.deepcopy(_RECORDED_AUDIT))
    _need(_same(value['facts'], facts), 'facts')
    _need(type(value['bindings']) is list and
          len(value['bindings']) == _FIXED['preservation_pairs'], 'retention')
    return value


def _source_rows(value):
    _keys(value, ('head','files'))
    _need(value['head'] == _FIXED['head'] and type(value['files']) is list and
          len(value['files']) == _FIXED['source_count'], 'source')
    result = {}
    for row in value['files']:
        _keys(row, ('path','bytes','sha256'))
        name = row['path']
        _need(type(name) is str and name and '\\' not in name and ':' not in name and
              not PurePosixPath(name).is_absolute() and
              all(p not in ('','.','..') for p in name.split('/')) and name not in result, 'source')
        pin = dict(row, path=str(Path(_FIXED['root'])/name))
        _binding(pin)
        result[name] = pin
    return result


def _source(reader, base):
    _git_identity()
    before = reader.json(base['product']['source_before'])
    after = reader.json(base['product']['source_after'])
    _need(_same(before, after), 'source_changed')
    rows = _source_rows(before)
    names = _git(['ls-files','-z']).decode('utf-8').split('\0')
    _need(names[-1] == '' and len(names[:-1]) == len(set(names[:-1])) == len(rows) and
          set(names[:-1]) == set(rows), 'source_roster')
    for pin in rows.values():
        reader.read(pin)
    reader.read(base['product']['source_archive'])


def _identity(value):
    _keys(value, ('pid','creation_filetime','executable'))
    _integer(value['pid']); _integer(value['creation_filetime'])
    _need(value['pid'] > 0 and value['creation_filetime'] > 0 and
          type(value['executable']) is str and Path(value['executable']).is_absolute(), 'identity')


def _meter(value):
    _keys(value, ('generated_bytes','controls_bytes'))
    _integer(value['generated_bytes']); _integer(value['controls_bytes'])
    _need(value['generated_bytes'] <= 3*1024**3 and value['controls_bytes'] <= 64*1024**2, 'meter')


def _execution(reader, base, records, *, jvm=False):
    request, owner, terminal = (records[k] for k in ('request','owner','terminal'))
    _keys(request, ('command','cwd','head','helper','source_archive','environment','owner',
                    'seconds','generated_limit_bytes','controls_limit_bytes'))
    _need(request['cwd'] == _FIXED['root'] and request['head'] == _FIXED['head'] and
          _same(request['source_archive'], base['product']['source_archive']), 'request')
    _integer(request['seconds'], 900)
    _integer(request['generated_limit_bytes'], 3*1024**3)
    _integer(request['controls_limit_bytes'], 64*1024**2)
    _keys(request['helper'], ('bytes','sha256'))
    _need(_same(request['helper'], {k:base['evidence']['helper'][k] for k in ('bytes','sha256')}), 'helper')
    _keys(request['environment'], _ENV_KEYS)
    _need(all(type(v) is str for v in request['environment'].values()) and
          all(request['environment'][k] == 'D:/Dev/_Temp' for k in ('TEMP','TMP','TMPDIR')), 'environment')
    _identity(request['owner'])
    expected_command = ([str(Path(_FIXED['root'])/'apps/android/gradlew.bat'), '-p',
        'apps/android','--offline','--no-daemon','--max-workers=2','--rerun-tasks',
        ':app:testDebugUnitTest'] if jvm else [request['owner']['executable'],
        '-I','-S','-B','scripts/check.py','android','--offline'])
    _need(_same(request['command'], expected_command), 'command')
    _keys(owner, ('status','cleanup_complete','elapsed_ms','worker_returncode','stdout_bytes',
                  'stderr_bytes','output_capture_complete'))
    _need(owner['status'] == 'child_exited' and owner['cleanup_complete'] is True and
          owner['output_capture_complete'] is True, 'owner')
    _integer(owner['worker_returncode'], 0); _integer(owner['elapsed_ms'])
    _need(owner['elapsed_ms'] <= 900000, 'owner')
    for role in ('stdout','stderr'):
        _integer(owner[role+'_bytes'], base['evidence'][role]['bytes'])
    _keys(terminal, ('passed','owner','source_equal','faults','samples','final_meter','source_count','source_archive'))
    _need(terminal['passed'] is True and terminal['source_equal'] is True and
          terminal['faults'] == [] and _same(terminal['owner'], owner) and
          _same(terminal['source_archive'], base['product']['source_archive']), 'terminal')
    _integer(terminal['source_count'], _FIXED['source_count'])
    _need(type(terminal['samples']) is list and 0 < len(terminal['samples']) <= 900, 'meter')
    for sample in (*terminal['samples'], terminal['final_meter']):
        _meter(sample)
    command_terminal = records['command_terminal']
    _keys(command_terminal, ('returncode','elapsed_ms'))
    _integer(command_terminal['returncode'], 0); _integer(command_terminal['elapsed_ms'])
    _need(command_terminal['elapsed_ms'] <= owner['elapsed_ms'], 'command')
    actual, command = records['actual_child'], records['command_child']
    _keys(actual, ('identity','helper')); _keys(command, ('identity','command'))
    _identity(actual['identity']); _identity(command['identity'])
    _need(_same(actual['helper'], request['helper']) and _same(command['command'], request['command']) and
          len({request['owner']['pid'], actual['identity']['pid'], command['identity']['pid']}) == 3, 'child')
    output = reader.read(base['evidence']['stdout'], data=True).decode('utf-8')
    _need('BUILD SUCCESSFUL' in output, 'audit')
    if jvm:
        lines = output.splitlines()
        _need('> Task :app:testDebugUnitTest' in lines and
              not any(line.startswith('> Task :app:testDebugUnitTest ') for line in lines) and
              '25 actionable tasks: 25 executed' in output, 'jvm_execution')
        return
    _need('81 actionable tasks: 10 executed, 71 up-to-date' in output, 'audit')
    # Decode preserved audit output; do not rerun APK, signature, ELF or DEX tools.
    start = output.index('{')
    _, consumed = json.JSONDecoder().raw_decode(output[start:])
    package = _json(output[start:start+consumed].encode('utf-8'))
    pair = _json(output.splitlines()[-1].encode('utf-8'))
    _keys(package, ('status','permissions','libraries'))
    _keys(pair, ('app','certificate_sha256','package','status','test','test_package','test_permissions'))
    audit = base['facts']['package_audit']
    _need(package['status'] == pair['status'] == 'passed' and
          _same(package['permissions'], audit['product_permissions']) and
          _same(package['libraries'], audit['libraries']) and
          pair['package'] == audit['package'] and pair['test_package'] == audit['test_package'] and
          pair['certificate_sha256'] == audit['certificate_sha256'] and
          _same(pair['test_permissions'], audit['test_permissions']), 'audit')
    for key, role in (('app','product_apk'), ('test','test_apk')):
        _keys(pair[key], ('bytes','sha256'))
        _need(_same(pair[key], {k:base['artifacts'][role][k] for k in ('bytes','sha256')}), 'audit')


def _retention(reader, base, reports):
    _keys(reports, ('version','mode','files','cases','tests','failures','errors','skipped','unique'))
    _integer(reports['version'], 1)
    _need(reports['mode'] == 'android' and _same(reports['files'], base['bindings']), 'retention')
    for key, expected in (('tests',579),('failures',0),('errors',0),('skipped',0),('unique',579)):
        _integer(reports[key], expected)
    _need(type(reports['cases']) is list and len(reports['cases']) == 579, 'reports')
    cases = set(); suites = set()
    for case in reports['cases']:
        _keys(case, ('suite','name','failure','errors','skipped'))
        _need(type(case['suite']) is str and case['suite'] and type(case['name']) is str and
              case['name'] and case['failure'] == [], 'reports')
        _integer(case['errors'], 0); _integer(case['skipped'], 0)
        cases.add((case['suite'], case['name'])); suites.add(case['suite'])
    _need(len(cases) == 579 and len(suites) == 69, 'reports')
    seen_source, seen_copy = set(), set()
    by_source = {}; xml = 0
    build = Path(_FIXED['root'])/'apps/android/app/build'
    phase = Path(_FIXED['capture'])/'android-v2'
    recovery = Path(_FIXED['recovery'])/'android-v2'
    extra = {str(build/suffix): recovery/suffix.replace('/','__') for suffix in (
        'reports/lint-results-debug.xml','outputs/apk/debug/app-debug.apk',
        'outputs/apk/androidTest/debug/app-debug-androidTest.apk',
        'generated/rustJniLibs/arm64-v8a/liblocallore_android.so',
        'generated/rustJniLibs/x86_64/liblocallore_android.so')}
    for pair in base['bindings']:
        _keys(pair, ('source','copy'))
        source, saved = pair['source'], pair['copy']
        _binding(source); _binding(saved)
        _need(source['path'] not in seen_source and saved['path'] not in seen_copy and
              _same({k:source[k] for k in ('bytes','sha256')},
                    {k:saved[k] for k in ('bytes','sha256')}), 'copy')
        seen_source.add(source['path']); seen_copy.add(saved['path'])
        path = Path(source['path'])
        if path.parent == build/'test-results/testDebugUnitTest':
            _need(path.name.startswith('TEST-') and path.suffix == '.xml', 'report_path')
            _pin_path(saved, phase/'reports'/path.name); xml += 1
        else:
            _need(source['path'] in extra, 'report_path')
            _pin_path(saved, extra[source['path']])
        # Both current and retained ordinary files remain part of the read graph.
        reader.read(source); reader.read(saved)
        by_source[source['path']] = source
    _need(xml == 69 and set(extra).issubset(seen_source), 'reports')
    for pin in base['artifacts'].values():
        _need(pin['path'] in by_source and _same(pin, by_source[pin['path']]), 'apk')
    for abi, pin in base['native'].items():
        # Only ordinary extracted/generated files, never Cargo release/deps aliases.
        _pin_path(pin, build/'generated/rustJniLibs'/abi/'liblocallore_android.so')
        _need(pin['path'] in by_source and _same(pin, by_source[pin['path']]), 'native')


def _jvm_proof(reader, base, value, final_reports):
    """Join preserved fresh execution metadata; never execute JVM/Gradle tools."""
    _keys(value, ('version','scope','head','source_count','evidence','report_bindings',
        'tests','suites','unique','failures','errors','skipped','actual_task_executed'))
    _integer(value['version'], 1)
    _need(value['scope'] == 'knowledge-ui-jvm-execution-v1' and
          value['head'] == _FIXED['head'] and value['actual_task_executed'] is True, 'jvm_execution')
    _integer(value['source_count'], _FIXED['source_count'])
    for key, expected in (('tests',579),('suites',69),('unique',579),
                          ('failures',0),('errors',0),('skipped',0)):
        _integer(value[key], expected)
    phase = Path(_FIXED['capture'])/'jvm-v1'
    paths = dict(request=phase/'request-v1.json', owner=phase/'owner-result-v1.json',
        terminal=phase/'terminal-v1.json', command_terminal=phase/'command-terminal-v1.json',
        stdout=phase/'owner-stdout-v1.bin', stderr=phase/'owner-stderr-v1.bin',
        actual_child=phase/'actual-child-v1.json', command_child=phase/'command-child-v1.json',
        source_before=phase/'source-before-v1.json', source_after=phase/'source-after-v1.json',
        report_preservation=phase/'report-preservation-v1.json',
        helper=Path(_FIXED['capture'])/'run-forced-jvm-v1.py',
        source_archive=Path(_FIXED['capture'])/('source-'+_FIXED['head']+'.zip'))
    _keys(value['evidence'], paths)
    for role, path in paths.items():
        _pin_path(value['evidence'][role], path)
    records = {}
    for role, pin in value['evidence'].items():
        if role in ('stdout','stderr','helper','source_archive'):
            reader.read(pin)
        else:
            records[role] = reader.json(pin)
    _need(_same(value['evidence']['source_archive'], base['product']['source_archive']) and
          _same(records['source_before'], records['source_after']) and
          _same(records['source_before'], reader.json(base['product']['source_before'])), 'jvm_source')
    _source_rows(records['source_before'])
    phase_base = dict(base, evidence=value['evidence'])
    _execution(reader, phase_base, records, jvm=True)
    reports = records['report_preservation']
    _keys(reports, ('version','mode','files','cases','tests','failures','errors','skipped','unique'))
    _integer(reports['version'], 1)
    _need(reports['mode'] == 'jvm' and
          _same(reports['files'], value['report_bindings']) and
          _same(reports['cases'], final_reports['cases']), 'jvm_reports')
    for key, expected in (('tests',579),('unique',579),('failures',0),('errors',0),('skipped',0)):
        _integer(reports[key], expected)
    _need(type(value['report_bindings']) is list and len(value['report_bindings']) == 69, 'jvm_reports')
    final_sources = {pair['source']['path']: pair['source'] for pair in base['bindings']}
    seen = set()
    report_root = Path(_FIXED['root'])/'apps/android/app/build/test-results/testDebugUnitTest'
    for pair in value['report_bindings']:
        _keys(pair, ('source','copy'))
        source, saved = pair['source'], pair['copy']
        _binding(source); _binding(saved)
        path = Path(source['path'])
        _need(path.parent == report_root and path.name.startswith('TEST-') and
              path.suffix == '.xml' and source['path'] not in seen and
              source['path'] in final_sources and _same(source, final_sources[source['path']]), 'jvm_reports')
        seen.add(source['path'])
        _pin_path(saved, phase/'reports'/path.name)
        _need(_same({k:source[k] for k in ('bytes','sha256')},
                    {k:saved[k] for k in ('bytes','sha256')}), 'jvm_reports')
        reader.read(source); reader.read(saved)


def _dex_proof(reader, base, value):
    """Validate fixed recorded parser results and hash their ordinary inputs."""
    _keys(value, ('version','scope','product_apk','test_apk','class_descriptor',
        'product_class_present','test_class_definitions','methods','native_entries',
        'packaged_native','script','android_runtime_executed','model_material'))
    _integer(value['version'], 1)
    _need(value['scope'] == 'knowledge-ui-dex-evidence-v1' and
          value['class_descriptor'] == 'Lorg/locallore/app/ui/KnowledgeRecordFilterScreenTest;' and
          value['product_class_present'] is False and
          value['android_runtime_executed'] is False and value['model_material'] is False, 'dex')
    _integer(value['test_class_definitions'], 1)
    for role in ('product_apk','test_apk'):
        _binding(value[role])
        _need(_same(value[role], base['artifacts'][role]), 'dex_apk')
        reader.read(value[role])
    _need(type(value['methods']) is list and len(value['methods']) == 4, 'dex_methods')
    expected = sorted(row[2] for row in ROSTER)
    methods = []
    for row in value['methods']:
        _keys(row, ('method','code_units','runtime_junit','public_instance','dex_entry'))
        _integer(row['code_units'])
        _need(row['code_units'] > 0 and row['runtime_junit'] is True and
              row['public_instance'] is True and row['dex_entry'] == 'classes4.dex', 'dex_methods')
        methods.append(row['method'])
    _need(_same(methods, expected), 'dex_methods')
    _keys(value['native_entries'], ('arm64-v8a','x86_64'))
    _keys(value['packaged_native'], ('arm64-v8a','x86_64'))
    build = Path(_FIXED['root'])/'apps/android/app/build'
    recovery = Path(_FIXED['recovery'])/'packaged-native-v1'
    for abi in ('arm64-v8a','x86_64'):
        entry = value['native_entries'][abi]
        _keys(entry, ('bytes','sha256'))
        pair = value['packaged_native'][abi]
        _keys(pair, ('source','copy'))
        source, saved = pair['source'], pair['copy']
        _pin_path(source, build/'intermediates/stripped_native_libs/debug/stripDebugDebugSymbols/out/lib'/abi/'liblocallore_android.so')
        _pin_path(saved, recovery/abi/'liblocallore_android.so')
        _need(_same(entry, {k:source[k] for k in ('bytes','sha256')}) and
              _same(entry, {k:saved[k] for k in ('bytes','sha256')}), 'dex_native')
        # Stripped APK entry bytes differ from generated debug-symbol bytes. Both
        # roles are read independently; neither grants old Cargo alias privileges.
        reader.read(source); reader.read(saved)
    _pin_path(value['script'], Path(_FIXED['capture'])/'inspect-dex-v1.py')
    reader.read(value['script'])


def _create_manifest(reader):
    base = _baseline(reader)
    _source(reader, base)
    records = {role:reader.json(pin) for role,pin in base['evidence'].items()
               if role not in ('stdout','stderr','helper')}
    for role in ('stdout','stderr','helper'):
        reader.read(base['evidence'][role])
    _execution(reader, base, records)
    _retention(reader, base, records['reports'])
    _jvm_proof(reader, base, records['jvm_execution'], records['reports'])
    _dex_proof(reader, base, records['dex'])
    _git_identity()
    reader.final()
    return dict(version=1, scope=SCOPE, mode=MODE, product=copy.deepcopy(base['product']),
        artifacts=copy.deepcopy(base['artifacts']), current_native_bindings=copy.deepcopy(base['native']),
        evidence=copy.deepcopy(base['evidence']), facts=copy.deepcopy(base['facts']),
        instrumentations=copy.deepcopy(ROSTER))


def create_manifest():
    """Return validated metadata; never write a manifest or infer authority."""
    try:
        return _create_manifest(_Reader())
    except BuildRefused:
        raise
    except (OSError, ValueError, KeyError, TypeError, IndexError, RecursionError,
            UnicodeError, subprocess.SubprocessError):
        raise BuildRefused('build') from None


def verify_frozen_product(artifacts):
    """Read the exact fixed APK pair/manifest; return independent validated data."""
    try:
        _keys(artifacts, ('build','product_apk','test_apk'))
        for pin in artifacts.values():
            _binding(pin)
        _pin_path(artifacts['build'], Path(_FIXED['manifest']))
        _need(artifacts['build']['bytes'] <= 2*1024**2 and
              type(_FIXED['apks']) is dict and
              all(_same(artifacts[role], _FIXED['apks'][role])
                  for role in ('product_apk','test_apk')), 'artifacts')
        reader = _Reader()
        actual = reader.json(artifacts['build'])
        expected = _create_manifest(reader)
        _need(_same(actual, expected), 'manifest')
        for role in ('product_apk','test_apk'):
            reader.read(artifacts[role])
        reader.final()
        return copy.deepcopy(expected)
    except BuildRefused:
        raise
    except (OSError, ValueError, KeyError, TypeError, IndexError, RecursionError,
            UnicodeError, subprocess.SubprocessError):
        raise BuildRefused('build') from None
