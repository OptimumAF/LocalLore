"""Source/document scope fences without importing any runtime owner.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import ast
from pathlib import Path, PureWindowsPath
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]


def literal_paths(path):
    values = {}
    def value(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.Name):
            return values[node.id]
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id in ('Path', 'PureWindowsPath') and len(node.args) == 1):
            return PureWindowsPath(value(node.args[0]))
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            return value(node.left) / value(node.right)
        raise ValueError('not a literal path')
    for node in ast.parse(path.read_text(encoding='utf-8')).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            try:
                values[node.targets[0].id] = value(node.value)
            except (ValueError, KeyError, TypeError):
                pass
    return values


class ProfileUiScopeDocumentTests(unittest.TestCase):
    def test_document_names_actual_source_guest_runtime_controls_and_helper(self):
        activation = literal_paths(ROOT / 'benchmarks/profile_ui_activation.py')
        contract = literal_paths(ROOT / 'benchmarks/owned_profile_ui_contract.py')
        doc = (ROOT / 'docs/native/PLAYER_PROFILE_UI_V1.md').read_text(encoding='utf-8')
        expected = {
            'Source': activation['SOURCE_ROOT'], 'Guest': contract['GUEST_ROOT'],
            'Runtime': activation['RUNTIME'], 'Controls': activation['CONTROLS'],
            'Helper': activation['HELPER'],
        }
        rows = re.findall(r'^- (Source|Guest|Runtime|Controls|Helper): `([^`]+)`\.$', doc, re.M)
        self.assertEqual(len(rows), 5)
        self.assertEqual({k: PureWindowsPath(v) for k, v in rows}, expected)
        self.assertEqual(activation['INPUT'], activation['CONTROLS'] / 'run-input-v1.json')
        self.assertEqual(activation['CONTROL'], activation['RUNTIME'] / 'control-v1')
        self.assertEqual(activation['HELPER'].parent, activation['SOURCE_ROOT'] / 'benchmarks')

if __name__ == '__main__':
    unittest.main()
