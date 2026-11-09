"""Read-only SDK12 documentation/source scope joins; no activation import.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import ast
from pathlib import Path, PurePosixPath
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]


def source_paths(relative, names):
    """Read only literal pathlib declarations and their local path composition."""
    tree = ast.parse((ROOT / relative).read_text(encoding='utf-8'))
    assignments = {
        target.id: node.value
        for node in tree.body if isinstance(node, ast.Assign)
        for target in node.targets if isinstance(target, ast.Name)
    }

    def literal(node):
        if isinstance(node, ast.Name):
            return literal(assignments[node.id])
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id in ('Path', 'PureWindowsPath')
                and len(node.args) == 1 and not node.keywords):
            value = ast.literal_eval(node.args[0])
            if type(value) is str:
                return PurePosixPath(value)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            value = ast.literal_eval(node.right)
            if type(value) is str:
                return literal(node.left) / value
        raise AssertionError('Scope declaration is no longer a literal path')

    return {name: str(literal(assignments[name])) for name in names}


class InventoryUiScopeDocumentationTests(unittest.TestCase):
    def test_documented_execution_paths_match_actual_activation_and_guest_authority(self):
        activation = source_paths('benchmarks/inventory_ui_activation.py',
                                  ('RUNTIME', 'CONTROLS', 'SOURCE_ROOT', 'HELPER'))
        guest = source_paths('benchmarks/owned_inventory_ui_contract.py', ('GUEST_ROOT',))
        document = (ROOT / 'docs/native/PLAYER_INVENTORY_UI_V1.md').read_text(encoding='utf-8')
        expected = {'Runtime': activation['RUNTIME'], 'Guest': guest['GUEST_ROOT'],
                    'Controls': activation['CONTROLS'], 'Helper': activation['HELPER']}
        # Check the prospective destinations as labelled roles, rather than
        # accepting an unrelated occurrence of an otherwise correct path.
        for label, path in expected.items():
            matches = re.findall(r'^- ' + label + r': `([^`]+)`\.$', document, re.MULTILINE)
            self.assertEqual(matches, [path], label + ' differs from authoritative source')
        roots = re.findall(r'The fixed activation helper runs from\s+`([^`]+)`\.', document)
        self.assertEqual(roots, [activation['SOURCE_ROOT']])
        self.assertEqual(activation['HELPER'],
                         str(PurePosixPath(activation['SOURCE_ROOT']) /
                             'benchmarks/inventory_ui_activation.py'))


if __name__ == '__main__':
    unittest.main()
