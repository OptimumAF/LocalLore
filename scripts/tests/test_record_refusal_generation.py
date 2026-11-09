"""Original generation/coherence oracles. Structural fake metadata never supplies approval."""
import builtins
import copy
import hashlib
from pathlib import Path, PureWindowsPath
import socket
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from benchmarks import owned_record_cancellation_ui_contract as profile
from benchmarks import record_cancellation_ui_activation as activation
from scripts import record_cancellation_ui_prepare_inputs as inspection
from scripts import record_cancellation_ui_fresh_contract as fresh
from scripts import record_cancellation_operation_contract as outer
from scripts import run_record_cancellation_ui_fresh as bridge
from scripts import run_record_cancellation_operation as operation


NEW = Path('D:/Dev/Experiments/LocalLore/2026-11-03-record-refusal-freeze-v1')
FROZEN = NEW/'frozen-profile-source-v1'
GUEST = Path('D:/Dev/Experiments/LocalLore/2026-11-03-record-refusal-ui-v1/avd-v1')
RUNTIME = Path('D:/Dev/Experiments/LocalLore/2026-11-03-record-refusal-ui-runtime-v1')
HEAD = 'dbcafb0070734cbccbd420a159f6305bc6f9090d'
TREE = '53c47a25b00f2ca868150f76d408c3789a6fcc3c'
B116 = Path('D:/Dev/Experiments/LocalLore/2026-11-03-record-cancellation-coherent-v1')
B116_FROZEN = B116/'frozen-profile-source-v1'
B116_GUEST = Path('D:/Dev/Experiments/LocalLore/2026-11-03-record-cancellation-ui-v1/avd-v1')
B116_RUNTIME = Path('D:/Dev/Experiments/LocalLore/2026-11-03-record-cancellation-ui-runtime-v1')
B116_HEAD = 'c89b9e4f73a5481a1ba5afd9808821e023d1cd0c'
B116_TREE = 'd29c520f60c2f21204fef0972d25f7d322ca368a'
B116_HANDOFF = dict(path=str(PureWindowsPath(B116)/'inspection-v1/frozen-inputs-v1.json'),
    bytes=9255, sha256='50e86854bcb5aeb3eb4c5c002e42c40bcf86285e869d8b99a51f95b8b73a0b7b')
B116_PREPARE = dict(path=str(PureWindowsPath(B116)/'inspection-v1/prepare-proposal-v1.json'),
    bytes=173620, sha256='fbfb3b37c089f7f662bd90762daf2c2c4e7a5d775a0bda8cdfaccede673c0afb')
B116_INNER = dict(bytes=29986, sha256='0a1f9feb5276fd96ac691b0757f264fe88f2aee158a91dc907c0d08f2e0fd198')
UNFROZEN_B120_INNER = dict(bytes=31655, sha256='1c7dac9aef00a7cdc0d5cdc49531802da96e61c14c7bff3aa622daa1a1163fbf')
B116_CONTRACT_SHA = '1762385e5bb660cc475cfde7af2040886061e6f057d6734cc6e01cdbcff93bab'


def pin(path):
    text = str(PureWindowsPath(path))
    return dict(path=text, bytes=101, sha256=hashlib.sha256(('B121 STRUCTURAL ONLY '+text).encode()).hexdigest())


def child_authority():
    return dict(version=1, scope='sdk18-fresh-prepare-and-one-record-cancellation-ui-run-v1',
        source_head=HEAD, proposal=pin(NEW/'PROPOSED_OPERATION.md'),
        operator=copy.deepcopy(outer.FRESH_OPERATOR), contract=copy.deepcopy(outer.FRESH_CONTRACT),
        handoff=copy.deepcopy(fresh.HANDOFF), ledger=pin('D:/Dev/_Migration/LocalLore-AVD-Storage/ledger-v1.json'),
        allow_sdk_prepare=True, allow_one_boot=True, allow_model=False, allow_retirement=False,
        approval_reference='SYNTHETIC B121 DATA ONLY; NOT HUMAN APPROVAL', max_operation_seconds=2400)


def parent_authority():
    return dict(version=1, scope='sdk18-record-cancellation-operation-authority-v1',
        profile_source_head=HEAD, operator=pin(NEW/'candidate-source-v1/scripts/run_record_cancellation_operation.py'),
        contract=pin(NEW/'candidate-source-v1/scripts/record_cancellation_operation_contract.py'),
        proposal=pin(NEW/'PROPOSED_OPERATION.md'), fresh_authority=pin(NEW/'human-authority-v1.json'),
        allow_one_operation=True, allow_model=False, allow_retirement=False,
        approval_reference='SYNTHETIC B121 DATA ONLY; NOT HUMAN APPROVAL', max_operation_seconds=2400)


def handoff():
    return dict(version=1, scope='sdk18-fresh-inputs-v1', source_root=str(FROZEN), source_head=HEAD,
        source_tree=TREE, guest=str(GUEST), controls=str(NEW/'run-controls-v1'), runtime=str(RUNTIME),
        sources=[pin(FROZEN/'benchmarks'/('source-%02d.py' % n)) for n in range(28)],
        python=dict(executable=pin('C:/Synthetic/python.exe'), runtime_dll=None),
        artifacts=dict(build=copy.deepcopy(fresh.BUILD_PIN), product_apk=pin('D:/Synthetic/product.apk'),
                       test_apk=pin('D:/Synthetic/test.apk')),
        prepare_proposal=copy.deepcopy(fresh.PREPARE_PIN),
        capacity_preview=pin(NEW/'inspection-v1/capacity-preview-v1.json'),
        profile=dict(memory_mib=8192, cores=4, api=35, max_run_seconds=1800),
        execution_authorized=False, model_material=False)


class RecordRefusalGenerationTests(unittest.TestCase):
    def accepted(self, validator, value):
        # Old generation refusal is an intended semantic failure, not a loader/API error.
        try:
            return validator(value)
        except (fresh.FreshRunRefused, outer.OperationRefused, inspection.PrepareInputsRefused):
            self.fail('the current B121 structural control was refused')

    def test_new_profile_uses_new_guest_runtime_and_frozen_role_without_a_new_sdk(self):
        self.assertEqual(PureWindowsPath(profile.GUEST_ROOT), PureWindowsPath(GUEST))
        self.assertEqual(activation.SOURCE_ROOT, FROZEN)
        self.assertEqual(activation.CONTROLS, NEW/'run-controls-v1')
        self.assertEqual(activation.RUNTIME, RUNTIME)
        self.assertEqual(activation.HELPER, FROZEN/'benchmarks/record_cancellation_ui_activation.py')
        self.assertNotEqual(PureWindowsPath(profile.GUEST_ROOT), PureWindowsPath(B116_GUEST))
        self.assertEqual(profile.CLIENT_VERSION, 18)
        self.assertEqual([row[0] for row in profile.INSTRUMENTATIONS],
                         ['record_cancel_1', 'record_cancel_2', 'record_cancel_3', 'record_cancel_4', 'record_cancel_5'])
        self.assertEqual((activation.OUTER_SECONDS, activation.OWNER_SECONDS), (1800, 1700))

    def test_cold_import_accepts_new_origins_but_never_b116_or_operator_origins(self):
        self.assertEqual(activation.SOURCE_ROOT, FROZEN)
        names = ('receipt_avd_environment', 'owned_record_cancellation_ui_contract',
            'owned_record_cancellation_ui_owner', 'owned_target_owner', 'isolated_adb_owner',
            'record_cancellation_ui_profile_build', 'record_cancellation_ui_controller',
            'android_process_record_cancellation_ui_verification')
        original_import = builtins.__import__
        for variant in ('current', 'b116-env', 'b116-build', 'operator-verification'):
            blocked = Mock(side_effect=AssertionError('unexpected operation or resource observation'))
            modules = {name: SimpleNamespace(__file__=str(FROZEN/'benchmarks'/(name+'.py')),
                prepare=blocked, execute=blocked, authorize=blocked) for name in names}
            if variant == 'b116-env': modules['receipt_avd_environment'].__file__ = str(B116_FROZEN/'benchmarks/receipt_avd_environment.py')
            elif variant == 'b116-build': modules['record_cancellation_ui_profile_build'].__file__ = str(B116_FROZEN/'benchmarks/record_cancellation_ui_profile_build.py')
            elif variant == 'operator-verification': modules['android_process_record_cancellation_ui_verification'].__file__ = str(NEW/'candidate-source-v1/benchmarks/android_process_record_cancellation_ui_verification.py')
            observed = []
            def importer(name, globals=None, locals=None, fromlist=(), level=0):
                if name == 'benchmarks' and fromlist:
                    self.assertTrue(set(fromlist) <= set(names)); observed.extend(fromlist)
                    return SimpleNamespace(**modules)
                return original_import(name, globals, locals, fromlist, level)
            before_path = list(sys.path)
            try:
                with self.subTest(variant=variant), patch.object(activation, '_MODULES', None), \
                     patch.object(builtins, '__import__', side_effect=importer), \
                     patch.object(Path, 'resolve', lambda path, **kwargs: path), \
                     patch.object(Path, 'open', blocked), patch.object(subprocess, 'Popen', blocked), \
                     patch.object(socket, 'socket', blocked):
                    if variant == 'current':
                        api = activation._api()
                        self.assertIs(api.env, modules['receipt_avd_environment'])
                        self.assertIs(api.build, modules['record_cancellation_ui_profile_build'])
                    else:
                        with self.assertRaises(activation.ActivationRefused): activation._api()
            finally:
                sys.path[:] = before_path
            self.assertEqual(observed, list(names))
            self.assertEqual(blocked.call_count, 0)

    def test_inspector_inner_and_outer_share_exact_sealed_role_catalog_and_count(self):
        for module in (inspection, fresh, outer):
            self.assertEqual(module.SOURCE, FROZEN)
        self.assertEqual(inspection.SOURCE_HEAD, HEAD)
        self.assertEqual(fresh.SOURCE_HEAD, HEAD)
        self.assertEqual(outer.FRESH_HEAD, HEAD)
        self.assertEqual(inspection.SOURCE_TREE, TREE)
        self.assertEqual(fresh.SOURCE_TREE, TREE)
        self.assertEqual(inspection._SOURCE_FILE_COUNT, 2671)
        self.assertEqual(bridge._SOURCE_FILE_COUNT, 2671)
        self.assertEqual(fresh.SOURCE_PUBLICATION, inspection.SOURCE_PUBLICATION)
        self.assertEqual(PureWindowsPath(fresh.SOURCE_PUBLICATION['path']), PureWindowsPath(NEW/'profile-source-publication-v1.json'))
        self.assertEqual(fresh.SOURCE_PUBLICATION['bytes'], 755007)
        self.assertEqual(fresh.SOURCE_PUBLICATION['sha256'], 'aa58a83cd42933165f659b454d768b3b6c4cbc4458efabf300704e09fd50de31')
        self.assertEqual(fresh.HANDOFF, outer.HANDOFF)
        self.assertEqual(PureWindowsPath(fresh.HANDOFF['path']), PureWindowsPath(NEW/'inspection-v1/frozen-inputs-v1.json'))
        self.assertNotEqual(fresh.HANDOFF['sha256'], B116_HANDOFF['sha256'])
        self.assertEqual(fresh.BUILD_PIN['bytes'], 32140)
        self.assertEqual(fresh.BUILD_PIN['sha256'], '4d39b74ad5aee455ce9060c01d760204022101e4b6b8ce58d12f666450d2894e')
        self.assertEqual(fresh.STATIC['bytes'], 3678)
        self.assertEqual(fresh.STATIC['sha256'], 'd2ca3f1ef02ed01169b84bb62090f663aca610db159e8db97606d1e1becccf99')

    def test_current_authorities_are_detached_data_and_b116_slots_do_not_borrow_consent(self):
        observed = Mock(side_effect=AssertionError('unexpected resource observation'))
        with patch.object(Path, 'open', observed), patch.object(builtins, 'open', observed), \
             patch.object(Path, 'stat', observed), patch.object(Path, 'lstat', observed), \
             patch.object(subprocess, 'Popen', observed), patch.object(socket, 'socket', observed):
            for rules, value, refused in ((fresh, child_authority(), fresh.FreshRunRefused),
                                          (outer, parent_authority(), outer.OperationRefused)):
                before = copy.deepcopy(value); returned = self.accepted(rules.validate_authority, value)
                self.assertEqual(returned, before); returned['operator']['sha256'] = '0'*64
                self.assertEqual(value, before)
                for role in ('proposal', 'operator', 'contract'):
                    bad = copy.deepcopy(value)
                    relative = PureWindowsPath(bad[role]['path']).relative_to(PureWindowsPath(NEW))
                    bad[role]['path'] = str(PureWindowsPath(B116)/relative)
                    with self.subTest(scope=rules.__name__, role=role), self.assertRaises(refused):
                        rules.validate_authority(bad)
                bad = copy.deepcopy(value); bad['source_head' if rules is fresh else 'profile_source_head'] = B116_HEAD
                with self.assertRaises(refused): rules.validate_authority(bad)
        self.assertEqual(observed.call_count, 0)

    def test_b116_guest_runtime_source_and_prepare_cannot_form_current_handoff(self):
        current = handoff(); self.assertEqual(self.accepted(fresh.validate_handoff, current), current)
        for field, old in (('guest', str(B116_GUEST)), ('runtime', str(B116_RUNTIME)),
                           ('controls', str(B116/'run-controls-v1')), ('source_root', str(B116_FROZEN)),
                           ('source_root', str(NEW/'candidate-source-v1')), ('source_head', B116_HEAD),
                           ('source_tree', B116_TREE)):
            bad = copy.deepcopy(current); bad[field] = old
            with self.subTest(field=field, old=old), self.assertRaises(fresh.FreshRunRefused):
                fresh.validate_handoff(bad)
        for field, old in (('prepare_proposal', B116_PREPARE),
                           ('capacity_preview', pin(B116/'inspection-v1/capacity-preview-v1.json'))):
            bad = copy.deepcopy(current); bad[field] = copy.deepcopy(old)
            with self.subTest(field=field), self.assertRaises(fresh.FreshRunRefused): fresh.validate_handoff(bad)
        self.assertIs(current['execution_authorized'], False)
        self.assertIs(current['model_material'], False)

    def test_retagging_old_handoff_bytes_is_not_refresh_and_identical_prepare_data_is_explicit(self):
        current = child_authority(); self.accepted(fresh.validate_authority, current)
        old_path = copy.deepcopy(current); old_path['handoff'] = copy.deepcopy(B116_HANDOFF)
        retagged = copy.deepcopy(current); retagged['handoff'] = dict(B116_HANDOFF, path=fresh.HANDOFF['path'])
        for label, bad in (('old-path', old_path), ('retagged-old-bytes', retagged)):
            with self.subTest(label=label), self.assertRaises(fresh.FreshRunRefused): fresh.validate_authority(bad)
        value = handoff(); self.accepted(fresh.validate_handoff, value)
        value['prepare_proposal'] = dict(B116_PREPARE, path=fresh.PREPARE_PIN['path'])
        if value['prepare_proposal'] == fresh.PREPARE_PIN:
            # Exact identical current data is allowed; it remains no execution authority.
            self.assertEqual(fresh.validate_handoff(value), value)
        else:
            with self.assertRaises(fresh.FreshRunRefused): fresh.validate_handoff(value)
        self.assertIs(value['execution_authorized'], False)

    def test_parent_rejects_b116_or_unrefreshed_inner_pins_before_invocation(self):
        parent, child = parent_authority(), child_authority()
        self.accepted(outer.validate_authority, parent); self.accepted(fresh.validate_authority, child)
        api = SimpleNamespace(env=SimpleNamespace(check_binding=Mock()), fresh_rules=fresh,
            probe=SimpleNamespace(_python_bindings=Mock(return_value={'fixture': 'python'})))
        invoke = Mock(side_effect=AssertionError('unexpected inner invocation'))
        with patch.object(operation, '_parts', return_value=(outer, api)), \
             patch.object(operation, '_bootstrap', return_value={'python': {'fixture': 'python'}}), \
             patch.object(operation, '_invoke_fresh', invoke):
            good = Mock(side_effect=[parent, child])
            with patch.object(operation, 'read', good):
                self.assertEqual(operation.read_authority(pin(NEW/'parent-authority-v1.json')), parent)
            self.assertEqual(good.call_count, 2)
            for variant in ('old-slot', 'b116-inner', 'unfrozen-b120-inner', 'old-contract', 'old-head'):
                a, b = copy.deepcopy(parent), copy.deepcopy(child)
                if variant == 'old-slot': a['fresh_authority'] = pin(B116/'human-authority-v1.json')
                elif variant in ('b116-inner', 'unfrozen-b120-inner'):
                    b['operator'] = dict(B116_INNER if variant == 'b116-inner' else UNFROZEN_B120_INNER,
                                         path=outer.FRESH_OPERATOR['path'])
                elif variant == 'old-contract': b['contract']['sha256'] = B116_CONTRACT_SHA
                else: b['source_head'] = B116_HEAD
                reads = Mock(side_effect=[a, b])
                with self.subTest(variant=variant), patch.object(operation, 'read', reads):
                    with self.assertRaises((outer.OperationRefused, fresh.FreshRunRefused)):
                        operation.read_authority(pin(NEW/'parent-authority-v1.json'))
                self.assertEqual(reads.call_count, 1 if variant == 'old-slot' else 2)
        self.assertEqual(invoke.call_count, 0)

    def test_new_catalog_headers_and_closed_members_refuse_before_payload_read(self):
        root = Path('D:/MemoryOnly/catalog')
        bodies = {'a.txt': b'', 'b.txt': b'hello\n'}
        rows = [dict(path=n, mode='100644', bytes=len(v), sha256=hashlib.sha256(v).hexdigest(),
                     git_blob=hashlib.sha1(b'blob '+str(len(v)).encode()+b'\0'+v).hexdigest())
                for n, v in bodies.items()]
        value = dict(final_commit=HEAD, final_tree=TREE, files=rows,
                     normal_preserved={'fixture': True}, shared_ledger_sha256='c'*64)
        reader = Mock(side_effect=lambda path, maximum: bodies[path.relative_to(root).as_posix()])
        # Tiny private validation port only. Public source_count must still be2671 (separate method).
        with patch.object(inspection, '_SOURCE_FILE_COUNT', 2):
            control = self.accepted(lambda v: inspection._verify_catalog(v, root, reader, list(bodies)), value)
            self.assertEqual(control, value); self.assertEqual(reader.call_count, 2)
            for variant in ('old-head', 'old-tree', 'missing', 'extra', 'foreign'):
                bad = copy.deepcopy(value)
                if variant == 'old-head': bad['final_commit'] = B116_HEAD
                elif variant == 'old-tree': bad['final_tree'] = B116_TREE
                elif variant == 'missing': bad['files'].pop()
                elif variant == 'extra': bad['files'].append(copy.deepcopy(rows[0]))
                else: bad['files'][0]['path'] = 'D:/B116/foreign.txt'
                attempted = Mock(side_effect=AssertionError('payload read before catalog refusal'))
                with self.subTest(variant=variant), self.assertRaises(inspection.PrepareInputsRefused):
                    inspection._verify_catalog(bad, root, attempted, [r['path'] for r in bad['files']])
                self.assertEqual(attempted.call_count, 0)
            for names in (['a.txt'], ['a.txt', 'b.txt', 'extra.txt']):
                attempted = Mock(side_effect=AssertionError('read before closed-member validation'))
                with self.assertRaises(inspection.PrepareInputsRefused):
                    inspection._verify_catalog(value, root, attempted, names)
                self.assertEqual(attempted.call_count, 0)
