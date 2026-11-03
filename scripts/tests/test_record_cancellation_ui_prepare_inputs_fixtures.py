"""Independent finite metadata construction for SDK18 inspection oracles.

No fixture opens the frozen profile, installed tools, credentials or a device.
The catalog graph has all 2644 rows; only its explicit reader port returns bytes.
"""
import copy
from contextlib import ExitStack
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest.mock import Mock, patch

PROFILE_HEAD = '287b158e72ed5c0811a2e7e433e73ada4f4d6c52'
PROFILE_TREE = '81dae478d06f2da8be5f14a693f276318fe0c4ac'
PROFILE_SOURCE = Path('D:/Dev/Experiments/LocalLore/2026-11-03-record-cancellation-profile-v1/candidate-source-v1')
GUEST = Path('D:/Dev/Experiments/LocalLore/2026-11-03-record-cancellation-ui-v1/avd-v1')
RUNTIME = Path('D:/Dev/Experiments/LocalLore/2026-11-03-record-cancellation-ui-runtime-v1')
CONTROLS = Path('D:/Dev/Experiments/LocalLore/2026-11-03-record-cancellation-profile-v1/run-controls-v1')
EMPTY_BLOB = 'e69de29bb2d1d6434b8b29ae775ad8c2e48c5391'
HELLO_BLOB = 'ce013625030ba8dba906f756967f9e9ca394464a'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class CatalogGraph:
    """Full-size private validator input, never a public source authority."""
    def __init__(self):
        self.root = Path('D:/Synthetic/sdk18-catalog')
        self.calls = []
        self.bodies = {}
        rows = []
        for index in range(2644):
            name = 'source-%04d.txt' % index
            body = b'hello\n' if index == 1 else b''
            self.bodies[name] = body
            rows.append(dict(path=name, mode='100755' if index == 1 else '100644',
                git_blob=HELLO_BLOB if index == 1 else EMPTY_BLOB,
                bytes=len(body), sha256=sha(body)))
        self.value = dict(final_commit=PROFILE_HEAD, final_tree=PROFILE_TREE,
            files=rows, normal_preserved=dict(head='8924278ce1c877e6d67c90c15a35fb23ca7198dc',
                status='', index_sha256='897c91824eb4ad6ecd5034e1eecb2874c34dfd499675763a4d44a4a55ba80119'),
            shared_ledger_sha256='84ad23a43f6c4abd6be82164fcec2e4e7b51277f1e250a507af22654be1a7294')

    @property
    def names(self):
        return [row['path'] for row in self.value['files']]

    @property
    def paths(self):
        return [self.root / name for name in self.names]

    def reader(self, path, maximum):
        path = Path(path)
        # Refuse before recording a foreign read: the caller's separate spy
        # still observes an attempted call if validation ever reaches here.
        relative = path.relative_to(self.root).as_posix()
        self.calls.append((relative, maximum))
        return self.bodies[relative]

    def detached(self):
        return copy.deepcopy(self.value)


class InspectionGraph:
    """Retained tiny private inspection graph; SDK/build/source ports are fake."""
    def __init__(self, subject, *, fits):
        self.s, self.fits = subject, fits

    def __enter__(self):
        from benchmarks import receipt_avd_environment as env
        from benchmarks import owned_record_cancellation_ui_contract as profile
        from benchmarks import record_cancellation_ui_profile_build as build
        from scripts.tests import test_record_cancellation_ui_profile_fixtures as product
        self.env, self.stack = env, ExitStack()
        self.base = Path(tempfile.mkdtemp(prefix='sdk18-inspection-metadata-'))
        self.output = self.base / 'inspection'
        self.tool = self.base / 'tool.bin'; self.tool.write_bytes(b'TOOL')
        self.ledger = self.base / 'isolated-ledger.json'; self.ledger.write_bytes(b'{"synthetic":true}\n')
        self.product = self.base / 'product.apk'; self.product.write_bytes(b'NOT AN APK PRODUCT')
        self.test = self.base / 'test.apk'; self.test.write_bytes(b'NOT AN APK TEST')
        self.manifest = product.raw_manifest(dict(product_apk=env.binding(self.product), test_apk=env.binding(self.test)))
        self.sources = [dict(path=str(self.s.SOURCE / 'benchmarks' / name), bytes=1,
            sha256=hashlib.sha256(name.encode()).hexdigest()) for name in sorted(profile.SOURCE_NAMES)]
        self.python = dict(executable=dict(path='C:\\Synthetic\\python.exe', bytes=1, sha256='b' * 64), runtime_dll=None)
        self.events, self.hash_passes = [], 0
        self.capacity = dict(version=1, scope='receipt-avd-prepare-capacity-preview-v1', root=str(self.s.GUEST),
            ledger=env.binding(self.ledger), max_guests=2, budget_bytes=64 * 1024**3, reservation_bytes=40 * 1024**3,
            active_count=0 if self.fits else 2, charged_bytes=0 if self.fits else 44 * 1024**3,
            projected_bytes=40 * 1024**3 if self.fits else 84 * 1024**3,
            root_limit_exceeded=not self.fits, byte_limit_exceeded=not self.fits,
            would_fit=self.fits, admission_granted=False)
        self.mutators = {name: Mock(side_effect=AssertionError('unexpected operational mutation'))
            for name in ('prepare', 'authorize', 'reserve_prepare', 'record_state', 'execute')}
        def binding(path):
            if Path(path) == self.s.REGISTRY / 'ledger-v1.json': return env.binding(self.ledger)
            return env.binding(path)
        def plan(guest, sdk, java, path, **kwargs):
            self.events.append('plan'); self.hash_passes += 1
            assert (guest, sdk, java) == (self.s.GUEST, self.s.SDK, self.s.JAVA)
            assert kwargs == dict(real_candidate=True, four_core_candidate=True)
            value = dict(phase='prepare', paths=dict(root=str(guest)), memory_mib=8192, cores=4,
                userdata_mib=12288, sdcard_mib=8192, allow_environment_calls=False, root_go_pending=True,
                bindings=[env.binding(self.tool)])
            env.create_json(path, value); return value
        def verify(proposal):
            self.events.append('verify'); self.hash_passes += 1
            assert proposal['bindings'] == [env.binding(self.tool)]
        self.api = SimpleNamespace(
            env=SimpleNamespace(binding=Mock(side_effect=binding), installation_files=Mock(return_value=[self.tool]),
                safe_path=env.safe_path, plan_prepare=Mock(side_effect=plan), validate_proposal=Mock(),
                verify_installation=Mock(side_effect=verify), check_external_state=Mock(), create_json=env.create_json,
                prepare=self.mutators['prepare'], authorize=self.mutators['authorize']),
            storage=SimpleNamespace(preview_prepare=Mock(side_effect=lambda _: copy.deepcopy(self.capacity)),
                reserve_prepare=self.mutators['reserve_prepare'], record_state=self.mutators['record_state']),
            contract=SimpleNamespace(source_bindings=Mock(return_value=self.sources)),
            probe=SimpleNamespace(_python_bindings=Mock(return_value=self.python)),
            build=SimpleNamespace(verify_frozen_product=Mock(return_value=self.manifest)),
            profile_build=SimpleNamespace(project_manifest=build.project_manifest),
            activation=SimpleNamespace(_source=Mock(), execute=self.mutators['execute']))
        original_physical = self.s._physical
        def physical(path, **kwargs):
            if path == self.s.GUEST.parent: return None  # Explicit ordinary-parent observation port.
            return original_physical(path, **kwargs)
        original_exists = self.s.os.path.lexists
        def exists(path):
            if Path(path) in (self.s.GUEST, self.s.RUNTIME, self.s.CONTROLS): return False
            return original_exists(path)
        self.catalog = CatalogGraph().value
        self.stack.enter_context(patch.object(self.s, '_physical', side_effect=physical))
        self.stack.enter_context(patch.object(self.s.os.path, 'lexists', side_effect=exists))
        self.stack.enter_context(patch.object(self.s, '_static', return_value=None))
        self.stack.enter_context(patch.object(self.s, '_raw', return_value=json.dumps(self.manifest).encode()))
        self.snapshot = self.stack.enter_context(patch.object(self.s, 'source_snapshot', return_value=self.catalog))
        return self

    def inspect(self):
        return self.s._inspect(self.api, self.catalog, self.output)

    def __exit__(self, *error):
        self.stack.close()  # Restore ports only; every tiny fixture file remains.
