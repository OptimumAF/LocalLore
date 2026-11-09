"""Original fixed SDK18 inspection oracles over finite explicit observation ports."""
import builtins
import copy
import io
import json
import os
from pathlib import Path
import socket
import subprocess
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from scripts import record_cancellation_ui_prepare_inputs as subject
from scripts.tests import test_record_cancellation_ui_prepare_inputs_fixtures as f


class RecordCancellationCatalogTests(unittest.TestCase):
    def test_full_2664_catalog_binds_literal_git_vectors_without_resource_observation(self):
        graph = f.CatalogGraph(); before = graph.detached()
        reader = Mock(wraps=graph.reader)
        observed = Mock(side_effect=AssertionError('unexpected resource observation'))
        with patch.object(Path, 'open', observed), patch.object(builtins, 'open', observed), \
             patch.object(socket, 'socket', observed), patch.object(subprocess, 'Popen', observed):
            returned = subject._verify_catalog(graph.value, graph.root, reader, graph.names)
        self.assertEqual(returned, before)
        returned['files'][0]['sha256'] = '0' * 64
        self.assertEqual(graph.value, before)
        self.assertEqual(reader.call_count, 2664)
        self.assertEqual(graph.value['files'][0]['git_blob'], 'e69de29bb2d1d6434b8b29ae775ad8c2e48c5391')
        self.assertEqual(graph.value['files'][1]['git_blob'], 'ce013625030ba8dba906f756967f9e9ca394464a')
        self.assertTrue(all(maximum == 16 * 1024**2 for _, maximum in graph.calls))
        self.assertEqual(observed.call_count, 0)

    def test_closed_catalog_shape_types_mode_and_case_aliases_fail_before_payload_reads(self):
        graph = f.CatalogGraph()
        for mutation in ('extra', 'head', 'tree', 'missing', 'duplicate', 'reordered', 'boolean_bytes', 'symlink_mode', 'oversize', 'aggregate', 'bad_blob'):
            value = graph.detached()
            if mutation == 'extra': value['caller_root'] = 'D:/Foreign'
            elif mutation == 'head': value['final_commit'] = 'a6ed7a989ad3f7fa679caca7f8d2ecc3e7d89035'
            elif mutation == 'tree': value['final_tree'] = '0' * 40
            elif mutation == 'missing': value['files'].pop()
            elif mutation == 'duplicate': value['files'][1]['path'] = value['files'][0]['path'].upper()
            elif mutation == 'reordered': value['files'].reverse()
            elif mutation == 'boolean_bytes': value['files'][0]['bytes'] = False
            elif mutation == 'symlink_mode': value['files'][0]['mode'] = '120000'
            elif mutation == 'oversize': value['files'][0]['bytes'] = 16 * 1024**2 + 1
            elif mutation == 'aggregate':
                for row in value['files'][:5]: row['bytes'] = 16 * 1024**2
            else: value['files'][0]['git_blob'] = True
            reader = Mock(side_effect=AssertionError('payload read after malformed catalog'))
            with self.subTest(mutation=mutation), self.assertRaises(subject.PrepareInputsRefused):
                subject._verify_catalog(value, graph.root, reader, graph.names)
            self.assertEqual(reader.call_count, 0)

    def test_foreign_and_noncanonical_row_paths_refuse_without_a_foreign_open_attempt(self):
        graph = f.CatalogGraph()
        for path in ('../outside.bin', 'a/../../outside.bin', 'D:/Foreign/secret.bin', '/absolute.txt',
                     'alias\\file.txt', 'n//file.txt', 'n/./file.txt', 'nul\x00file.txt'):
            value = graph.detached(); value['files'][0]['path'] = path
            reader = Mock(side_effect=AssertionError('foreign reader attempted'))
            with self.subTest(path=path), self.assertRaises(subject.PrepareInputsRefused):
                subject._verify_catalog(value, graph.root, reader, [r['path'] for r in value['files']])
            self.assertEqual(reader.call_count, 0)
        for names in (graph.names[:-1], graph.names + ['unlisted.txt']):
            reader = Mock(side_effect=AssertionError('closed set must precede reads'))
            with self.assertRaises(subject.PrepareInputsRefused):
                subject._verify_catalog(graph.value, graph.root, reader, names)
            self.assertEqual(reader.call_count, 0)

    def test_same_length_and_newline_drift_cannot_pass_the_raw_sha_and_git_blob_checks(self):
        for changed in (b'HELLO\n', b'hello\r\n', bytearray(b'hello\n')):
            graph = f.CatalogGraph(); graph.bodies['source-0001.txt'] = changed
            reader = Mock(wraps=graph.reader)
            with self.subTest(changed=changed), self.assertRaises(subject.PrepareInputsRefused):
                subject._verify_catalog(graph.value, graph.root, reader, graph.names)
            self.assertEqual(reader.call_count, 2)
        graph = f.CatalogGraph(); graph.value['files'][0]['git_blob'] = '0' * 40
        reader = Mock(wraps=graph.reader)
        with self.assertRaises(subject.PrepareInputsRefused):
            subject._verify_catalog(graph.value, graph.root, reader, graph.names)
        self.assertEqual(reader.call_count, 1)

    def test_fixed_snapshot_rechecks_catalog_bytes_after_all_payloads_and_rejects_extra_dirs(self):
        for changed in (False, True):
            graph = f.CatalogGraph(); graph.root = subject.SOURCE
            catalog = json.dumps(graph.value, sort_keys=True).encode()
            reader = Mock(wraps=graph.reader)
            with patch.object(subject, '_raw', side_effect=[catalog, catalog + b' ' if changed else catalog]) as seal, \
                 patch.object(subject, '_walk', return_value=(graph.names, [])) as walk, \
                 patch.object(subject, '_source_bytes', reader):
                if changed:
                    with self.assertRaises(subject.PrepareInputsRefused): subject.source_snapshot()
                else: self.assertEqual(subject.source_snapshot(), graph.value)
            self.assertEqual(seal.call_count, 2)
            self.assertTrue(all(call.args == (subject.SOURCE_PUBLICATION,) for call in seal.call_args_list))
            self.assertEqual(walk.call_count, 1)
            self.assertEqual(reader.call_count, 2664)
        graph = f.CatalogGraph(); reader = Mock()
        with patch.object(subject, '_raw', return_value=json.dumps(graph.value).encode()), \
             patch.object(subject, '_walk', return_value=(graph.names, ['unlisted-empty-directory'])), \
             patch.object(subject, '_source_bytes', reader):
            with self.assertRaises(subject.PrepareInputsRefused): subject.source_snapshot()
        self.assertEqual(reader.call_count, 0)

    def test_walk_refuses_link_observations_before_traversal_or_payload_open(self):
        class Entries:
            def __init__(self, values): self.values = values
            def __enter__(self): return iter(self.values)
            def __exit__(self, *error): pass
        root = Path('D:/Synthetic/walk')
        for kind in ('ordinary', 'symlink', 'reparse'):
            entry = SimpleNamespace(path=str(root / 'file'), is_symlink=Mock(return_value=kind == 'symlink'),
                is_dir=Mock(return_value=False))
            scan = Mock(return_value=Entries([entry]))
            opened = Mock(side_effect=AssertionError('walk must never open a payload'))
            with patch.object(subject, '_physical'), patch.object(subject.os, 'scandir', scan), \
                 patch.object(Path, 'resolve', lambda path, **kw: path), \
                 patch.object(Path, 'lstat', return_value=SimpleNamespace(st_file_attributes=1024 if kind == 'reparse' else 0)), \
                 patch.object(Path, 'open', opened):
                if kind == 'ordinary': self.assertEqual(subject._walk(root), (['file'], []))
                else:
                    with self.assertRaises(subject.PrepareInputsRefused): subject._walk(root)
            self.assertEqual(scan.call_count, 1)
            self.assertEqual(opened.call_count, 0)
            self.assertEqual(entry.is_dir.call_count, 1 if kind == 'ordinary' else 0)


class RecordCancellationInspectionBoundaryTests(unittest.TestCase):
    def test_installed_catalog_limits_are_checked_before_hash_or_planning_attempts(self):
        gib = 1024**3
        variants = [('exact', 2048, [6 * gib] + [0] * 2047),
                    ('count', 2049, [0] * 2049), ('bytes', 2, [6 * gib, 1]),
                    ('bool', 1, [True]), ('duplicate', 2, [1, 1])]
        for kind, count, sizes in variants:
            paths = [Path('C:/Synthetic/Installed') / ('file-%04d' % i) for i in range(count)]
            if kind == 'duplicate': paths[1] = paths[0]
            position = {path: i for i, path in enumerate(paths)}
            safe = Mock(side_effect=lambda path: SimpleNamespace(stat=lambda: SimpleNamespace(st_size=sizes[position[path]])))
            plan = Mock(side_effect=AssertionError('no planning in stat gate'))
            api = SimpleNamespace(env=SimpleNamespace(installation_files=Mock(return_value=paths), safe_path=safe,
                plan_prepare=plan, binding=Mock(side_effect=AssertionError('no hash before budget'))))
            if kind == 'exact':
                self.assertEqual(subject._installed_files(api), (paths, 6 * gib))
                self.assertEqual(safe.call_count, 2048)
            else:
                with self.subTest(kind=kind), self.assertRaises(subject.PrepareInputsRefused): subject._installed_files(api)
                self.assertEqual(safe.call_count, {'count': 0, 'bytes': 2, 'bool': 1, 'duplicate': 0}[kind])
            api.env.installation_files.assert_called_once_with(subject.SDK, subject.JAVA)
            self.assertEqual(plan.call_count, 0)
            self.assertEqual(api.env.binding.call_count, 0)

    def test_adb_key_remains_path_metadata_and_python_mismatch_precedes_pin_observation(self):
        def pin(name):
            return dict(path='D:\\Synthetic\\' + name, bytes=1, sha256='a' * 64)
        python = dict(executable=pin('python.exe'), runtime_dll=None)
        value = {name: pin(name) for name in ('adb', 'capabilities', 'source_review', 'compatibility',
            'emulator', 'qemu', 'refuser', 'refuser_source')}
        value.update(tools=[pin('tool.dll')], python=python, auth_key_path='C:\\Synthetic\\PRIVATE_ADB_KEY')
        check = Mock(); binding = Mock(return_value=value['refuser_source'])
        api = SimpleNamespace(env=SimpleNamespace(check_binding=check, binding=binding))
        forbidden = Mock(side_effect=AssertionError('credential observation'))
        with patch.object(subject, '_raw', return_value=json.dumps(value).encode()) as static, \
             patch.object(Path, 'open', forbidden), patch.object(Path, 'stat', forbidden):
            subject._static(api, python)
        self.assertEqual(static.call_args.args, (subject.STATIC,))
        expected = [value[k] for k in ('adb', 'capabilities', 'source_review', 'compatibility', 'emulator', 'qemu', 'refuser', 'refuser_source')]
        expected += value['tools'] + [python['executable']]
        self.assertEqual([call.args[0] for call in check.call_args_list], expected)
        binding.assert_called_once_with(subject.SOURCE / 'benchmarks/native/deny_adb_client.c')
        self.assertEqual(forbidden.call_count, 0)
        self.assertTrue(all(call.args[0]['path'] != value['auth_key_path'] for call in check.call_args_list))
        check.reset_mock(); wrong = copy.deepcopy(python); wrong['executable']['sha256'] = '0' * 64
        with patch.object(subject, '_raw', return_value=json.dumps(value).encode()):
            with self.assertRaises(subject.PrepareInputsRefused): subject._static(api, wrong)
        self.assertEqual(check.call_count, 0)

    def test_public_inspection_and_cli_offer_no_root_output_or_execution_override(self):
        graph = f.CatalogGraph(); api = object(); events = []
        result = dict(execution_authorized=False, sdk_dispatched=False, model_material=False)
        with patch.object(subject, 'source_snapshot', side_effect=lambda: events.append('source') or graph.value) as source, \
             patch.object(subject, '_parts', side_effect=lambda: events.append('parts') or api) as parts, \
             patch.object(subject, '_inspect', side_effect=lambda *args: events.append('inspect') or result) as inspect:
            self.assertIs(subject.inspect_fixed(), result)
            self.assertEqual(events, ['source', 'parts', 'inspect'])
            inspect.assert_called_once_with(api, graph.value, subject.OUTPUT)
            source.reset_mock(); parts.reset_mock(); inspect.reset_mock()
            with self.assertRaises(TypeError): subject.inspect_fixed(output='D:/Foreign')
            for argv in ([], ['run'], ['inspect', '--output', 'D:/Foreign'], ['inspect', '--authority', 'anything']):
                with self.subTest(argv=argv): self.assertEqual(subject.main(argv), 2)
            self.assertEqual(source.call_count, 0)
            self.assertEqual(parts.call_count, 0)
            self.assertEqual(inspect.call_count, 0)
        with patch.object(subject, 'inspect_fixed', return_value=result) as inspect, \
             patch.object(subject.sys, 'stdout', io.StringIO()) as stdout:
            self.assertEqual(subject.main(['inspect']), 0)
            self.assertEqual(json.loads(stdout.getvalue()), result)
        self.assertEqual(inspect.call_count, 1)


@unittest.skipUnless(os.name == 'nt', 'retained private inspection fixture requires physical D')
class RecordCancellationInspectionFlowTests(unittest.TestCase):
    def test_fit_and_blocked_inspection_both_publish_only_four_data_records_and_no_consent(self):
        for fits in (False, True):
            with self.subTest(fits=fits), f.InspectionGraph(subject, fits=fits) as graph:
                result = graph.inspect()
                self.assertEqual({p.name for p in graph.output.iterdir()}, {'prepare-proposal-v1.json',
                    'capacity-preview-v1.json', 'frozen-inputs-v1.json', 'inspection-result-v1.json'})
                handoff = graph.env.read_json(result['handoff']['path'])
                preview = graph.env.read_json(result['capacity']['path'])
                self.assertEqual(preview['would_fit'], fits)
                self.assertIs(preview['admission_granted'], False)
                self.assertIs(handoff['execution_authorized'], False)
                self.assertIs(handoff['model_material'], False)
                self.assertEqual(handoff['artifacts']['build'], subject.BUILD)
                self.assertEqual(handoff['source_head'], 'c89b9e4f73a5481a1ba5afd9808821e023d1cd0c')
                self.assertEqual(result['source_files'], 2664)
                self.assertEqual(result['benchmark_sources'], 28)
                self.assertEqual((result['installed_files'], result['installed_bytes_per_pass'], result['installed_hash_passes']), (1, 4, 2))
                self.assertEqual(graph.hash_passes, 2)
                self.assertIs(result['execution_authorized'], False)
                self.assertIs(result['sdk_dispatched'], False)
                self.assertIs(result['model_material'], False)
                self.assertEqual(graph.api.env.plan_prepare.call_count, 1)
                self.assertEqual(graph.api.env.verify_installation.call_count, 1)
                self.assertEqual(graph.api.activation._source.call_count, 1)
                self.assertTrue(all(port.call_count == 0 for port in graph.mutators.values()))

    def test_late_capacity_or_ledger_change_preserves_partial_plan_without_publishing_handoff(self):
        for changed in ('capacity', 'ledger'):
            with self.subTest(changed=changed), f.InspectionGraph(subject, fits=False) as graph:
                if changed == 'capacity':
                    second = copy.deepcopy(graph.capacity); second['charged_bytes'] += 1
                    graph.api.storage.preview_prepare.side_effect = [copy.deepcopy(graph.capacity), second]
                else:
                    verify = graph.api.env.verify_installation.side_effect
                    def drift(proposal):
                        verify(proposal)
                        with graph.ledger.open('ab') as stream: stream.write(b' ')
                    graph.api.env.verify_installation.side_effect = drift
                with self.assertRaises(subject.PrepareInputsRefused): graph.inspect()
                self.assertEqual({p.name for p in graph.output.iterdir()}, {'prepare-proposal-v1.json'})
                self.assertTrue(all(port.call_count == 0 for port in graph.mutators.values()))
                self.assertEqual(graph.api.env.plan_prepare.call_count, 1)
                with self.assertRaises(subject.PrepareInputsRefused): graph.inspect()
                self.assertEqual(graph.api.env.plan_prepare.call_count, 1)

    def test_late_source_refusal_keeps_planning_data_but_never_writes_an_inspection_success(self):
        with f.InspectionGraph(subject, fits=False) as graph:
            graph.snapshot.side_effect = subject.PrepareInputsRefused('source')
            with self.assertRaises(subject.PrepareInputsRefused): graph.inspect()
            self.assertEqual({p.name for p in graph.output.iterdir()}, {'prepare-proposal-v1.json', 'capacity-preview-v1.json'})
            self.assertEqual(graph.api.activation._source.call_count, 0)
            self.assertTrue(all(port.call_count == 0 for port in graph.mutators.values()))
