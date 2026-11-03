"""Original SDK18 closed-authority oracles; no record represents real consent."""
import builtins
import copy
import hashlib
from pathlib import Path, PureWindowsPath
import socket
import subprocess
import unittest
from unittest.mock import Mock, patch

from scripts import record_cancellation_ui_fresh_contract as fresh
from scripts import record_cancellation_operation_contract as parent

HEAD = 'dbcafb0070734cbccbd420a159f6305bc6f9090d'
TREE = '53c47a25b00f2ca868150f76d408c3789a6fcc3c'
OUT = PureWindowsPath('D:/Dev/Experiments/LocalLore/2026-11-03-record-refusal-freeze-v1')


def pin(path):
    text = str(PureWindowsPath(str(path)))
    return dict(path=text, bytes=101, sha256=hashlib.sha256(('SDK18 STRUCTURAL FIXTURE ' + text).encode()).hexdigest())


def fresh_authority():
    return dict(version=1, scope='sdk18-fresh-prepare-and-one-record-cancellation-ui-run-v1',
        source_head=HEAD, proposal=pin(fresh.PROPOSAL), operator=pin(fresh.OPERATOR),
        contract=pin(fresh.CONTRACT), handoff=copy.deepcopy(fresh.HANDOFF),
        ledger=pin(fresh.REGISTRY / 'ledger-v1.json'), allow_sdk_prepare=True,
        allow_one_boot=True, allow_model=False, allow_retirement=False,
        approval_reference='SYNTHETIC STRUCTURAL TEST ONLY; NOT HUMAN APPROVAL', max_operation_seconds=2400)


def parent_authority():
    return dict(version=1, scope='sdk18-record-cancellation-operation-authority-v1',
        profile_source_head=HEAD, operator=pin(parent.OPERATOR), contract=pin(parent.CONTRACT),
        proposal=pin(parent.PROPOSAL), fresh_authority=pin(parent.FRESH_AUTHORITY),
        allow_one_operation=True, allow_model=False, allow_retirement=False,
        max_operation_seconds=2400, approval_reference='SYNTHETIC STRUCTURAL TEST ONLY; NOT HUMAN APPROVAL')


class RecordCancellationFreshContractTests(unittest.TestCase):
    def test_fixed_profile_anchor_and_separate_authority_slots_return_detached_values(self):
        self.assertEqual(fresh.SOURCE_HEAD, HEAD)
        self.assertEqual(fresh.SOURCE_TREE, TREE)
        self.assertEqual(PureWindowsPath(fresh.AUTHORITY), OUT / 'human-authority-v1.json')
        self.assertEqual(PureWindowsPath(parent.AUTHORITY), OUT / 'parent-authority-v1.json')
        self.assertEqual(PureWindowsPath(parent.FRESH_AUTHORITY), OUT / 'human-authority-v1.json')
        self.assertEqual(PureWindowsPath(fresh.LIVE), OUT / 'live-operation-v1')
        self.assertEqual(PureWindowsPath(parent.LIVE), OUT / 'live-parent-v1')
        self.assertEqual(fresh.MAX_SECONDS, 2400)
        self.assertEqual(parent.MAX_SECONDS, 2400)
        for rules, make in ((fresh, fresh_authority), (parent, parent_authority)):
            value = make(); before = copy.deepcopy(value)
            returned = rules.validate_authority(value)
            self.assertEqual(returned, before)
            returned['operator']['sha256'] = '0' * 64
            self.assertEqual(value, before)

    def test_authority_mutations_cannot_borrow_sdk17_or_observe_any_resource(self):
        attempted = Mock(side_effect=AssertionError('unexpected resource observation'))
        cases = ((fresh, fresh_authority, fresh.FreshRunRefused), (parent, parent_authority, parent.OperationRefused))
        with patch.object(Path, 'open', attempted), patch.object(builtins, 'open', attempted), \
             patch.object(socket, 'socket', attempted), patch.object(subprocess, 'Popen', attempted):
            for rules, make, refused in cases:
                valid = make(); rules.validate_authority(valid)
                for mutation in ('version', 'scope', 'head', 'model', 'retirement', 'allow', 'seconds', 'operator', 'extra', 'old_head_key'):
                    bad = copy.deepcopy(valid)
                    if mutation == 'version': bad['version'] = True
                    elif mutation == 'scope': bad['scope'] = 'sdk17-diagnostic-operation-authority-v1'
                    elif mutation == 'head': bad['source_head' if rules is fresh else 'profile_source_head'] = 'a6ed7a989ad3f7fa679caca7f8d2ecc3e7d89035'
                    elif mutation == 'model': bad['allow_model'] = 0
                    elif mutation == 'retirement': bad['allow_retirement'] = True
                    elif mutation == 'allow': bad['allow_sdk_prepare' if rules is fresh else 'allow_one_operation'] = 1
                    elif mutation == 'seconds': bad['max_operation_seconds'] = 2400.0
                    elif mutation == 'operator': bad['operator'] = pin('D:/Foreign/caller.py')
                    elif mutation == 'extra': bad['registry'] = 'D:/Foreign/registry'
                    else: bad['operator_head' if rules is fresh else 'fresh_head'] = '0' * 40
                    with self.subTest(rules=rules.__name__, mutation=mutation), self.assertRaises(refused):
                        rules.validate_authority(bad)
        self.assertEqual(attempted.call_count, 0)

    def test_one_use_attempt_joins_all_current_pins_and_refuses_boolean_no_retry(self):
        for rules, make, scope, roles, refused in (
            (fresh, fresh_authority, 'sdk18-fresh-operation-attempt-v1', ('handoff', 'operator', 'contract'), fresh.FreshRunRefused),
            (parent, parent_authority, 'sdk18-record-cancellation-operation-attempt-v1', ('operator', 'contract', 'fresh_authority'), parent.OperationRefused),
        ):
            authority = make(); authority_pin = pin(rules.AUTHORITY)
            attempt = dict(version=1, scope=scope, authority=authority_pin, no_retry=True,
                **{role: copy.deepcopy(authority[role]) for role in roles})
            returned = rules.validate_attempt(attempt, authority_pin, authority)
            self.assertEqual(returned, attempt)
            returned['authority']['sha256'] = '0' * 64
            self.assertNotEqual(returned, attempt)
            for mutation in ('version', 'retry', 'authority', *roles, 'extra'):
                bad = copy.deepcopy(attempt)
                if mutation == 'version': bad['version'] = True
                elif mutation == 'retry': bad['no_retry'] = 1
                elif mutation == 'extra': bad['allow_retry'] = True
                else: bad[mutation]['sha256'] = '0' * 64
                with self.subTest(scope=scope, mutation=mutation), self.assertRaises(refused):
                    rules.validate_attempt(bad, authority_pin, authority)

    def test_contract_top_level_and_validation_do_not_open_paths_or_dispatch(self):
        # Read the ordinary source before installing the no-observation ports;
        # only replay its top-level pure definition/constant construction here.
        sources = [(Path(module.__file__), Path(module.__file__).read_bytes()) for module in (fresh, parent)]
        attempted = Mock(side_effect=AssertionError('import-time observation'))
        with patch.object(Path, 'open', attempted), patch.object(builtins, 'open', attempted), \
             patch.object(Path, 'stat', attempted), patch.object(Path, 'lstat', attempted), \
             patch.object(socket, 'socket', attempted), patch.object(subprocess, 'Popen', attempted):
            for path, source in sources:
                namespace = dict(__file__=str(path), __name__='sdk18_pure_definition_fixture')
                exec(compile(source, str(path), 'exec'), namespace)
                make = fresh_authority if path.name == 'record_cancellation_ui_fresh_contract.py' else parent_authority
                self.assertEqual(namespace['validate_authority'](make()), make())
        self.assertEqual(attempted.call_count, 0)
